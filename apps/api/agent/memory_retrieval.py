"""
memory_retrieval.py — Retrieval helpers for the memory backbone.

Functions:
  - search_my_history(user_id, query, k)  → Qdrant semantic search over session_chunks
  - topics_in_session(session_id)         → all topics touched in a session
  - sessions_for_topic(topic_name)        → all sessions that touched a topic (recursive subtopics)
  - get_weakness_profile(user_id)         → weakness_profiles rows with topic names joined
"""
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ── Lazy singletons ──────────────────────────────────────────────────────────

_supabase = None
def get_supabase():
    global _supabase
    if _supabase is None:
        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_SERVICE_KEY", os.getenv("SUPABASE_ANON_KEY", ""))
        if url and key:
            try:
                from supabase import create_client
                _supabase = create_client(url, key)
            except Exception as e:
                logger.warning(f"Supabase init failed in memory_retrieval: {e}")
    return _supabase


_embeddings = None
def get_embeddings():
    global _embeddings
    if _embeddings is None:
        try:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            _embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
        except Exception as e:
            logger.warning(f"Embeddings init failed: {e}")
    return _embeddings


_qdrant = None
def get_qdrant():
    global _qdrant
    if _qdrant is None:
        try:
            from qdrant_client import QdrantClient
            url = os.getenv("QDRANT_URL", "http://localhost:6333")
            _qdrant = QdrantClient(url=url, timeout=3)
            _qdrant.get_collections()  # connectivity check
        except Exception as e:
            logger.warning(f"Qdrant unavailable in memory_retrieval: {e}")
    return _qdrant


# ── Retrieval helpers ─────────────────────────────────────────────────────────

async def search_my_history(user_id: str, query: str, k: int = 5) -> list[dict]:
    """Semantic search over user's session_chunks in Qdrant."""
    emb = get_embeddings()
    qdrant = get_qdrant()
    if not emb or not qdrant:
        return []
    try:
        vector = await emb.aembed_query(query)
        results = qdrant.search(
            collection_name="session_chunks",
            query_vector=vector,
            query_filter={"must": [{"key": "user_id", "match": {"value": user_id}}]},
            limit=k,
        )
        return [
            {
                "text": r.payload.get("text", ""),
                "session_id": r.payload.get("session_id"),
                "topics": r.payload.get("topics", []),
                "score": r.score,
            }
            for r in results
        ]
    except Exception as e:
        logger.warning(f"search_my_history failed: {e}")
        return []


def topics_in_session(session_id: str) -> list[dict]:
    """Return all topics touched in a session (via user_topic_events)."""
    sb = get_supabase()
    if not sb:
        return []
    try:
        res = (
            sb.table("user_topic_events")
            .select("topic_id, topics(name)")
            .eq("session_id", session_id)
            .eq("kind", "studied")
            .execute()
        )
        seen = set()
        out = []
        for row in res.data or []:
            tid = row.get("topic_id")
            if tid and tid not in seen:
                seen.add(tid)
                name = row.get("topics", {})
                if isinstance(name, dict):
                    name = name.get("name", tid)
                out.append({"topic_id": tid, "name": name})
        return out
    except Exception as e:
        logger.warning(f"topics_in_session failed: {e}")
        return []


def sessions_for_topic(topic_name: str, user_id: str) -> list[dict]:
    """Return all sessions where this topic (or its subtopics) was studied."""
    sb = get_supabase()
    if not sb:
        return []
    try:
        # Find topic_id by name
        topic_res = sb.table("topics").select("id").eq("name", topic_name).execute()
        if not topic_res.data:
            return []
        topic_id = topic_res.data[0]["id"]

        # Get all sessions that touched this topic for this user
        res = (
            sb.table("user_topic_events")
            .select("session_id, sessions(title, started_at)")
            .eq("topic_id", topic_id)
            .eq("user_id", user_id)
            .execute()
        )
        seen = set()
        out = []
        for row in res.data or []:
            sid = row.get("session_id")
            if sid and sid not in seen:
                seen.add(sid)
                sess = row.get("sessions", {}) or {}
                out.append({
                    "session_id": sid,
                    "title": sess.get("title", "Untitled Session"),
                    "started_at": sess.get("started_at"),
                })
        return out
    except Exception as e:
        logger.warning(f"sessions_for_topic failed: {e}")
        return []


def get_weakness_profile(user_id: str) -> list[dict]:
    """Return weakness_profiles with topic names joined."""
    sb = get_supabase()
    if not sb:
        return []
    try:
        res = (
            sb.table("weakness_profiles")
            .select("mastery, last_seen, topics(name)")
            .eq("user_id", user_id)
            .order("mastery", desc=False)
            .execute()
        )
        out = []
        for row in res.data or []:
            topic = row.get("topics", {}) or {}
            out.append({
                "topic": topic.get("name", "Unknown"),
                "mastery": row.get("mastery", 0.0),
                "last_seen": row.get("last_seen"),
            })
        return out
    except Exception as e:
        logger.warning(f"get_weakness_profile failed: {e}")
        return []
