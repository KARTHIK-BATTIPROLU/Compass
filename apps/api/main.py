import asyncio
import json
import logging
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List
from langchain_core.messages import HumanMessage
from agent.graph import graph
from routers import messages, health, quiz

logger = logging.getLogger(__name__)

app = FastAPI(title="LearnForge API")

# ── CORS ────────────────────────────────────────────────────────────────────
# Restrict to known web origin in production; allow localhost in dev.
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


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


async def dummy_token_generator():
    tokens = ["Hello, ", "this ", "is ", "a ", "streaming ", "test ", "from ", "the ", "agent!"]
    for token in tokens:
        yield f"data: {token}\n\n"
        await asyncio.sleep(0.3)


@app.get("/api/test/stream")
def test_stream():
    return StreamingResponse(dummy_token_generator(), media_type="text/event-stream")


# ── Chat endpoint ───────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    session_id: str
    prompt: str
    modes: List[str] = []


@app.post("/api/chat/stream")
async def chat_stream(req: Request, chat_req: ChatRequest):
    # Validate inputs
    if not chat_req.session_id or not chat_req.session_id.strip():
        async def err():
            yield f"data: {json.dumps({'error': 'session_id is required'})}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(err(), media_type="text/event-stream")

    if not chat_req.prompt or len(chat_req.prompt.strip()) == 0:
        async def err():
            yield f"data: {json.dumps({'error': 'prompt cannot be empty'})}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(err(), media_type="text/event-stream")

    if len(chat_req.prompt) > 8000:
        async def err():
            yield f"data: {json.dumps({'error': 'prompt exceeds maximum length'})}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(err(), media_type="text/event-stream")

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

        try:
            async for event in graph.astream_events(inputs, version="v2"):
                kind = event["event"]

                # Stream text tokens
                if kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if chunk.content:
                        yield f"data: {json.dumps({'type': 'token', 'content': chunk.content})}\n\n"

                # Forward artifact events from nodes
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
            # Log full detail server-side; send safe message to client
            logger.error(f"Graph execution error for session {chat_req.session_id}: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'content': 'An error occurred processing your request. Please try again.'})}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
