import asyncio
import json
import logging
import os
from dotenv import load_dotenv
load_dotenv()

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from typing import List
from langchain_core.messages import HumanMessage
from agent.graph import get_compiled_graph, CHECKPOINTS_DB
from agent.auth import get_current_user, user_owns_session
from routers import messages, health, quiz, memory, curriculum, export

logger = logging.getLogger(__name__)

# ── Checkpointer lifecycle ───────────────────────────────────────────────────
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

_checkpointer = None


def _prune_old_checkpoints(db_path: str, max_age_days: int = 14) -> None:
    """Delete checkpoint/write rows older than max_age_days. Best-effort —
    failures are logged, never fatal to startup.

    LangGraph checkpoint_ids are UUID6 (see
    langgraph.checkpoint.base.id.uuid6): time-ordered, so a lexicographic
    string comparison against a reference UUID6 built for the cutoff
    timestamp works as an age filter without needing a separate timestamp
    column."""
    import sqlite3
    import time as time_module

    if not os.path.exists(db_path):
        return
    try:
        from langgraph.checkpoint.base.id import UUID

        cutoff_100ns = (time_module.time_ns() - max_age_days * 86400 * 10**9) // 100 + 0x01B21DD213814000
        uuid_int = ((cutoff_100ns >> 12) & 0xFFFFFFFFFFFF) << 80
        uuid_int |= (cutoff_100ns & 0x0FFF) << 64
        # clock_seq=0, node=0 -> smallest possible UUID6 at this timestamp,
        # so real checkpoint_ids from the same instant still sort >= it.
        cutoff_id = str(UUID(int=uuid_int, version=6))

        conn = sqlite3.connect(db_path)
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM checkpoints WHERE checkpoint_id < ?", (cutoff_id,))
            deleted_checkpoints = cur.rowcount
            cur.execute("DELETE FROM writes WHERE checkpoint_id < ?", (cutoff_id,))
            deleted_writes = cur.rowcount
            conn.commit()
        finally:
            conn.close()
        if deleted_checkpoints or deleted_writes:
            logger.info(f"Pruned {deleted_checkpoints} checkpoint(s) and {deleted_writes} write(s) older than {max_age_days} days")
    except Exception as e:
        logger.warning(f"Checkpoint prune failed (non-fatal): {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _checkpointer
    _prune_old_checkpoints(CHECKPOINTS_DB)
    async with AsyncSqliteSaver.from_conn_string(CHECKPOINTS_DB) as saver:
        _checkpointer = saver
        yield
    _checkpointer = None

def get_graph():
    """Returns a graph compiled with the active checkpointer."""
    if _checkpointer is None:
        # Fallback: compile without checkpointer (e.g. tests / startup race)
        from agent.graph import graph
        return graph
    return get_compiled_graph(_checkpointer)


# ── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(title="LearnForge API", lifespan=lifespan)

# ── CORS ─────────────────────────────────────────────────────────────────────
WEB_ORIGIN = os.getenv("WEB_ORIGIN", "http://localhost:3000")
ADDITIONAL_ORIGINS = os.getenv("ADDITIONAL_ORIGINS", "").split(",")
allowed_origins = [WEB_ORIGIN] + [o.strip() for o in ADDITIONAL_ORIGINS if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(messages.router)
app.include_router(health.router)
app.include_router(quiz.router)
app.include_router(memory.router)
app.include_router(curriculum.router)
app.include_router(export.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "checkpointer": "sqlite" if _checkpointer else "none"}


@app.get("/api/download/anki/{filename}")
def download_anki(filename: str):
    filepath = os.path.join(os.path.dirname(__file__), "data", "downloads", filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(filepath, media_type="application/apkg", filename=filename)


@app.get("/api/test/stream")
def test_stream():
    async def gen():
        for token in ["Hello, ", "streaming ", "works!"]:
            yield f"data: {token}\n\n"
            await asyncio.sleep(0.2)
    return StreamingResponse(gen(), media_type="text/event-stream")


# ── Chat endpoint ─────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    session_id: str
    prompt: str
    modes: List[str] = []


@app.post("/api/chat/stream")
async def chat_stream(req: Request, chat_req: ChatRequest, user = Depends(get_current_user)):
    # ── Input validation ────────────────────────────────────────────────────
    if not chat_req.session_id or not chat_req.session_id.strip():
        async def _err():
            yield f"data: {json.dumps({'type': 'error', 'content': 'session_id is required'})}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(_err(), media_type="text/event-stream")

    if not user_owns_session(user.id, chat_req.session_id):
        async def _err():
            yield f"data: {json.dumps({'type': 'error', 'content': 'Forbidden: You do not own this session'})}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(_err(), media_type="text/event-stream", status_code=403)

    if not chat_req.prompt or not chat_req.prompt.strip():
        async def _err():
            yield f"data: {json.dumps({'type': 'error', 'content': 'prompt cannot be empty'})}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(_err(), media_type="text/event-stream")

    if len(chat_req.prompt) > 8000:
        async def _err():
            yield f"data: {json.dumps({'type': 'error', 'content': 'prompt too long (max 8000 chars)'})}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(_err(), media_type="text/event-stream")

    async def event_generator():
        inputs = {
            "session_id": chat_req.session_id,
            "prompt": chat_req.prompt,
            "modes": chat_req.modes,
            "messages": [HumanMessage(content=chat_req.prompt)],
            "curriculum_ctx": [],
            "artifacts": [],
            "topics_touched": [],
            "citations": [],
        }

        # thread_id = session_id so each session has its own durable state
        config = {"configurable": {"thread_id": chat_req.session_id}}

        try:
            g = get_graph()
            async for event in g.astream_events(inputs, config=config, version="v2"):
                kind = event["event"]

                # Stream text tokens — but only from the node actually generating
                # the user-facing response. astream_events fires
                # on_chat_model_stream for EVERY chat-model call in the graph,
                # including memory_writer's internal topic-extraction LLM call;
                # forwarding those unfiltered leaked raw extraction JSON into
                # the visible chat message.
                if kind == "on_chat_model_stream":
                    node = event.get("metadata", {}).get("langgraph_node")
                    if node == "memory_writer":
                        continue
                    chunk = event["data"]["chunk"]
                    if chunk.content:
                        yield f"data: {json.dumps({'type': 'token', 'content': chunk.content})}\n\n"

                # Forward artifact / citation events
                elif kind == "on_chain_end":
                    output = event.get("data", {}).get("output", {})
                    if isinstance(output, dict):
                        artifacts = output.get("artifacts", [])
                        if artifacts:
                            yield f"data: {json.dumps({'type': 'artifacts', 'data': artifacts})}\n\n"
                        citations = output.get("citations", [])
                        if citations:
                            yield f"data: {json.dumps({'type': 'citations', 'data': citations})}\n\n"
                        nudge = output.get("nudge")
                        if nudge:
                            yield f"data: {json.dumps({'type': 'nudge', 'data': nudge})}\n\n"

        except Exception as e:
            # Full detail logged server-side; safe message to client
            logger.error(
                f"Graph error — session={chat_req.session_id}: {e}", exc_info=True
            )
            yield f"data: {json.dumps({'type': 'error', 'content': 'An error occurred. Please try again.'})}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
