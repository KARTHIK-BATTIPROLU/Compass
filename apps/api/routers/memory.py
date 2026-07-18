"""
routers/memory.py — API endpoints for memory retrieval.

GET /api/memory/topics/{session_id}       → topics touched in a session
GET /api/memory/sessions/{topic_name}     → sessions for a topic
GET /api/memory/history?q=...             → semantic search over user's history
GET /api/memory/weakness                  → user's weakness profile
"""
from fastapi import APIRouter, Query, Depends, HTTPException
from agent.memory_retrieval import (
    search_my_history,
    topics_in_session,
    sessions_for_topic,
    get_weakness_profile,
)
from agent.memory_summarizer import maybe_summarize_session
import os
from agent.auth import get_current_user, user_owns_session

router = APIRouter(prefix="/api/memory", tags=["memory"])


@router.get("/sessions/mine")
async def list_my_sessions(user = Depends(get_current_user)):
    """Lists the current user's sessions, lazily generating a summary for
    any session that just became eligible (>=4 messages, no summary yet).
    This is the summarizer's trigger point — see agent/memory_summarizer.py."""
    from agent.auth import get_supabase
    sb = get_supabase()
    if not sb:
        return {"sessions": []}

    res = (
        sb.table("sessions")
        .select("id, title, summary, started_at, class_level")
        .eq("user_id", user.id)
        .order("started_at", desc=True)
        .execute()
    )
    sessions = res.data or []

    for s in sessions:
        summary = await maybe_summarize_session(sb, s["id"], user.id, s.get("summary"))
        s["summary"] = summary

    return {"sessions": sessions}


@router.get("/topics/{session_id}")
def get_topics_in_session(session_id: str, user = Depends(get_current_user)):
    """Return all topics studied in a given session."""
    if not user_owns_session(user.id, session_id):
        raise HTTPException(status_code=403, detail="Forbidden")
    return {"session_id": session_id, "topics": topics_in_session(session_id)}


@router.get("/sessions")
def get_sessions_for_topic(
    topic: str = Query(..., description="Topic name to look up"),
    user = Depends(get_current_user),
):
    """Return all sessions where this topic was studied."""
    return {"topic": topic, "sessions": sessions_for_topic(topic, user.id)}


@router.get("/history")
async def get_history(
    q: str = Query(..., description="Search query"),
    k: int = Query(5, ge=1, le=20),
    user = Depends(get_current_user),
):
    """Semantic search over user's session history."""
    results = await search_my_history(user.id, q, k)
    return {"query": q, "results": results}


@router.get("/weakness")
def get_weakness(user = Depends(get_current_user)):
    """Return user's weakness profile ranked by mastery (lowest first)."""
    return {"user_id": user.id, "weakness": get_weakness_profile(user.id)}
