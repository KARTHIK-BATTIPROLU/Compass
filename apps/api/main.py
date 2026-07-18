import asyncio
import json
import logging
import os
from dotenv import load_dotenv
load_dotenv()

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from typing import List
from langchain_core.messages import HumanMessage
from agent.graph import get_compiled_graph, CHECKPOINTS_DB
from routers import messages, health, quiz, memory, curriculum

logger = logging.getLogger(__name__)

# ── Checkpointer lifecycle ───────────────────────────────────────────────────
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

_checkpointer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _checkpointer
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
async def chat_stream(req: Request, chat_req: ChatRequest):
    # ── Input validation ────────────────────────────────────────────────────
    if not chat_req.session_id or not chat_req.session_id.strip():
        async def _err():
            yield f"data: {json.dumps({'type': 'error', 'content': 'session_id is required'})}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(_err(), media_type="text/event-stream")

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

                # Stream text tokens
                if kind == "on_chat_model_stream":
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

        except Exception as e:
            # Full detail logged server-side; safe message to client
            logger.error(
                f"Graph error — session={chat_req.session_id}: {e}", exc_info=True
            )
            yield f"data: {json.dumps({'type': 'error', 'content': 'An error occurred. Please try again.'})}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
