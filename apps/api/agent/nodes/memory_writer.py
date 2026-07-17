"""
memory_writer.py — Real implementation.

On every turn:
  1. Extract topics from the conversation using Gemini (JSON output).
  2. Upsert topics → topic_edges → user_topic_events in Postgres (via Supabase).
  3. Embed the turn text and upsert into Qdrant `session_chunks` collection.
  4. Persist the raw user + assistant messages to the `messages` table.

Non-fatal: any failure logs a warning and the turn continues normally.
"""
import uuid
import json
import logging
import os
from typing import Optional

from agent.state import AppState
from langfuse import observe

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
                logger.warning(f"Supabase init failed: {e}")
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
            from qdrant_client.models import VectorParams, Distance
            url = os.getenv("QDRANT_URL", "http://localhost:6333")
            client = QdrantClient(url=url, timeout=3)
            # Ensure session_chunks collection exists
            existing = {c.name for c in client.get_collections().collections}
            if "session_chunks" not in existing:
                client.create_collection(
                    collection_name="session_chunks",
                    vectors_config=VectorParams(size=768, distance=Distance.COSINE),
                )
            _qdrant = client
        except Exception as e:
            logger.warning(f"Qdrant unavailable for memory_writer: {e}")
    return _qdrant


# ── Topic extraction ─────────────────────────────────────────────────────────

async def _extract_topics(prompt: str, response_text: str) -> list[str]:
    """Use Gemini to extract 1-5 topic names from the turn. Returns [] on failure."""
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import SystemMessage, HumanMessage

        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.0)
        extraction_prompt = f"""Extract 1-5 specific academic topic names from this conversation turn.
Return ONLY a JSON array of strings, nothing else. Example: ["Photosynthesis", "Chlorophyll"]

User prompt: {prompt[:500]}
Assistant response (first 500 chars): {response_text[:500]}"""

        result = await llm.ainvoke([HumanMessage(content=extraction_prompt)])
        text = result.content.strip()
        # Strip markdown code block if present
        if "```" in text:
            text = text.split("```")[1].replace("json", "").strip()
        topics = json.loads(text)
        return [t for t in topics if isinstance(t, str)][:5]
    except Exception as e:
        logger.warning(f"Topic extraction failed: {e}")
        return []


# ── Postgres helpers ──────────────────────────────────────────────────────────

def _upsert_topic(sb, name: str) -> Optional[str]:
    """Upsert a topic by name, return its UUID."""
    try:
        res = sb.table("topics").select("id").eq("name", name).execute()
        if res.data:
            return res.data[0]["id"]
        new_id = str(uuid.uuid4())
        sb.table("topics").insert({"id": new_id, "name": name}).execute()
        return new_id
    except Exception as e:
        logger.warning(f"Topic upsert failed for '{name}': {e}")
        return None


def _record_topic_event(sb, user_id: str, topic_id: str, session_id: str, kind: str = "studied"):
    try:
        sb.table("user_topic_events").insert({
            "user_id": user_id,
            "topic_id": topic_id,
            "session_id": session_id,
            "kind": kind,
        }).execute()
    except Exception as e:
        logger.warning(f"Topic event insert failed: {e}")


def _save_messages(sb, session_id: str, prompt: str, ai_msg: str, modes: list):
    try:
        rows = [{"session_id": session_id, "role": "user", "content": prompt, "modes": modes}]
        if ai_msg:
            rows.append({"session_id": session_id, "role": "assistant", "content": ai_msg, "modes": modes})
        sb.table("messages").insert(rows).execute()
    except Exception as e:
        logger.warning(f"Message save failed: {e}")


# ── Qdrant chunk upsert ───────────────────────────────────────────────────────

async def _embed_and_store(session_id: str, user_id: str, topics: list[str], text: str):
    """Embed the turn text and upsert into Qdrant session_chunks."""
    emb = get_embeddings()
    qdrant = get_qdrant()
    if not emb or not qdrant:
        return
    try:
        vector = await emb.aembed_query(text[:2000])
        from qdrant_client.models import PointStruct
        qdrant.upsert(
            collection_name="session_chunks",
            points=[PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "session_id": session_id,
                    "user_id": user_id,
                    "topics": topics,
                    "text": text[:1000],
                },
            )],
        )
    except Exception as e:
        logger.warning(f"Qdrant session chunk upsert failed: {e}")


# ── Main node ─────────────────────────────────────────────────────────────────

@observe()
async def memory_writer_node(state: AppState) -> dict:
    session_id = state.get("session_id")
    prompt = state.get("prompt", "")
    modes = state.get("modes", [])
    messages = state.get("messages", [])
    user = state.get("user", {})

    # Find last assistant message
    ai_msg = ""
    for msg in reversed(messages):
        if hasattr(msg, "type") and msg.type == "ai":
            ai_msg = msg.content
            break
        if hasattr(msg, "role") and getattr(msg, "role", None) == "assistant":
            ai_msg = msg.content
            break

    sb = get_supabase()
    if not sb or not session_id:
        return {}

    # Get user_id from session
    user_id = None
    try:
        res = sb.table("sessions").select("user_id").eq("id", session_id).execute()
        if res.data:
            user_id = res.data[0].get("user_id")
    except Exception as e:
        logger.warning(f"Could not fetch user_id for session {session_id}: {e}")

    # 1. Save messages
    _save_messages(sb, session_id, prompt, ai_msg, modes)

    # 2. Extract topics
    topics = await _extract_topics(prompt, ai_msg)
    topic_ids = []
    if topics and user_id:
        for name in topics:
            tid = _upsert_topic(sb, name)
            if tid:
                topic_ids.append(tid)
                _record_topic_event(sb, user_id, tid, session_id, "studied")

    # 3. Embed turn and store in Qdrant
    turn_text = f"Q: {prompt}\nA: {ai_msg}"
    if user_id:
        await _embed_and_store(session_id, user_id, topics, turn_text)

    # Return updated topics_touched
    current_topics = state.get("topics_touched", [])
    return {"topics_touched": list(set(current_topics + topics))}
