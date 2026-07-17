"""
routers/memory.py — API endpoints for memory retrieval.

GET /api/memory/topics/{session_id}       → topics touched in a session
GET /api/memory/sessions/{topic_name}     → sessions for a topic
GET /api/memory/history?q=...             → semantic search over user's history
GET /api/memory/weakness                  → user's weakness profile
"""
from fastapi import APIRouter, Query
from agent.memory_retrieval import (
    search_my_history,
    topics_in_session,
    sessions_for_topic,
    get_weakness_profile,
)
import os

router = APIRouter(prefix="/api/memory", tags=["memory"])


@router.get("/topics/{session_id}")
def get_topics_in_session(session_id: str):
    """Return all topics studied in a given session."""
    return {"session_id": session_id, "topics": topics_in_session(session_id)}


@router.get("/sessions")
def get_sessions_for_topic(
    topic: str = Query(..., description="Topic name to look up"),
    user_id: str = Query(..., description="User ID"),
):
    """Return all sessions where this topic was studied."""
    return {"topic": topic, "sessions": sessions_for_topic(topic, user_id)}


@router.get("/history")
async def get_history(
    q: str = Query(..., description="Search query"),
    user_id: str = Query(..., description="User ID"),
    k: int = Query(5, ge=1, le=20),
):
    """Semantic search over user's session history."""
    results = await search_my_history(user_id, q, k)
    return {"query": q, "results": results}


@router.get("/weakness")
def get_weakness(user_id: str = Query(..., description="User ID")):
    """Return user's weakness profile ranked by mastery (lowest first)."""
    return {"user_id": user_id, "weakness": get_weakness_profile(user_id)}
