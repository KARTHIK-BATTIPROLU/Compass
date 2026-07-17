import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from langgraph.types import Command
from pydantic import BaseModel, Field

from app.auth.models import UserPublic
from app.auth.routes import get_current_user
from app.agent.graph import get_graph
from app.agent.nodes.weak_spot_tracker import update_weak_spot
from app.db.mongo_client import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agent", tags=["agent"])


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    role: Optional[str] = None
    thread_id: Optional[str] = None


class ReviewRequest(BaseModel):
    thread_id: str
    action: str  # approve | edit | regenerate
    content: Optional[dict[str, Any]] = None
    target: Optional[str] = None
    instruction: Optional[str] = None


class QuizAnswerRequest(BaseModel):
    topic: str
    concept: str
    correct: bool
    question: Optional[str] = None


def _sse(data: dict[str, Any]) -> str:
    return f"data: {json.dumps(data, default=str)}\n\n"


async def _stream_graph(
    user: UserPublic,
    message: str,
    thread_id: str,
) -> AsyncIterator[str]:
    graph = get_graph()
    config = {"configurable": {"thread_id": thread_id}}
    initial: dict[str, Any] = {
        "user_input": message,
        "user_id": user.id,
        "user_role": user.role.value,
        "detected_intents": [],
        "generated_content": {},
        "scraped_content": [],
        "needs_human_review": False,
        "messages": [],
        "errors": [],
        "thread_id": thread_id,
    }

    yield _sse({"type": "thread", "thread_id": thread_id})
    yield _sse({"type": "node_start", "node": "graph"})

    try:
        async for event in graph.astream(initial, config=config, stream_mode="updates"):
            for node_name, update in event.items():
                if node_name == "__interrupt__":
                    yield _sse({"type": "status", "message": "awaiting human review"})
                    continue
                yield _sse({"type": "node_start", "node": node_name})
                if node_name == "scraper_node":
                    yield _sse({"type": "status", "message": "searching the web..."})
                if isinstance(update, dict):
                    if "detected_intents" in update:
                        yield _sse(
                            {
                                "type": "intents",
                                "intents": update["detected_intents"],
                            }
                        )
                    if "generated_content" in update:
                        yield _sse(
                            {
                                "type": "content",
                                "content": update["generated_content"],
                            }
                        )
                    if update.get("messages"):
                        for m in update["messages"]:
                            yield _sse({"type": "message", "message": m})
                yield _sse({"type": "node_end", "node": node_name})

        state = await graph.aget_state(config)
        values = state.values or {}
        interrupted = bool(state.next)
        yield _sse(
            {
                "type": "final",
                "thread_id": thread_id,
                "needs_human_review": True,
                "detected_intents": values.get("detected_intents", []),
                "generated_content": values.get("generated_content", {}),
                "scraped_content": [
                    {
                        "url": s.get("url"),
                        "title": s.get("title"),
                        "error": s.get("error"),
                        "markdown": (s.get("markdown") or "")[:500],
                    }
                    for s in (values.get("scraped_content") or [])
                ],
                "errors": values.get("errors", []),
                "interrupted": interrupted,
            }
        )
        yield _sse({"type": "done"})
    except Exception as exc:
        logger.exception("Graph stream failed")
        yield _sse({"type": "error", "message": str(exc)})
        yield _sse({"type": "done"})


@router.post("/chat")
async def chat(body: ChatRequest, user: UserPublic = Depends(get_current_user)):
    thread_id = body.thread_id or str(uuid.uuid4())
    return StreamingResponse(
        _stream_graph(user, body.message, thread_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/approve")
async def approve(body: ReviewRequest, user: UserPublic = Depends(get_current_user)):
    return await _resume_review(body, user, default_action="approve")


@router.post("/edit")
async def edit(body: ReviewRequest, user: UserPublic = Depends(get_current_user)):
    return await _resume_review(body, user, default_action="edit")


@router.post("/regenerate")
async def regenerate(body: ReviewRequest, user: UserPublic = Depends(get_current_user)):
    return await _resume_review(body, user, default_action="regenerate")


async def _resume_review(body: ReviewRequest, user: UserPublic, default_action: str):
    graph = get_graph()
    config = {"configurable": {"thread_id": body.thread_id}}
    action = body.action or default_action
    decision = {
        "action": action,
        "content": body.content,
        "target": body.target,
        "instruction": body.instruction
        or (
            "The user rejected the previous output, try again differently."
            if action == "regenerate"
            else None
        ),
    }

    final_content: dict[str, Any] = {}
    events: list[dict[str, Any]] = []

    try:
        async for event in graph.astream(
            Command(resume=decision),
            config=config,
            stream_mode="updates",
        ):
            for node_name, update in event.items():
                events.append({"node": node_name, "update_keys": list(update.keys()) if isinstance(update, dict) else []})
                if isinstance(update, dict) and "generated_content" in update:
                    final_content = update["generated_content"]
    except Exception as exc:
        logger.exception("Resume failed")
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    state = await graph.aget_state(config)
    values = state.values or {}
    content = values.get("generated_content") or final_content

    if action in ("approve", "edit"):
        db = get_db()
        now = datetime.now(timezone.utc)
        for content_type, payload in content.items():
            if content_type in ("grounding_used", "sources"):
                continue
            if isinstance(payload, dict) and payload.get("error"):
                continue
            await db.generated_docs.insert_one(
                {
                    "user_id": user.id,
                    "content_type": content_type,
                    "content": payload,
                    "status": "approved" if action == "approve" else "edited",
                    "created_at": now,
                    "updated_at": now,
                    "thread_id": body.thread_id,
                }
            )

    # If still interrupted (regenerate loop), surface content again
    return {
        "ok": True,
        "action": action,
        "thread_id": body.thread_id,
        "generated_content": content,
        "detected_intents": values.get("detected_intents", []),
        "needs_human_review": values.get("needs_human_review", False),
        "review_status": values.get("review_status"),
        "events": events,
    }


@router.post("/submit-quiz-answer")
async def submit_quiz_answer(body: QuizAnswerRequest, user: UserPublic = Depends(get_current_user)):
    result = await update_weak_spot(user.id, body.topic, body.concept, body.correct)
    return result
