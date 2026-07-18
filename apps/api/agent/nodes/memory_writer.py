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

async def _extract_topics_with_parents(prompt: str, response_text: str, prior_topics: list[str]) -> list[dict]:
    """Use Gemini to extract 1-5 topic names from the turn. When a topic is a
    specific subtopic of one of `prior_topics` (topics already touched earlier
    in this session), also return that as `parent` — this is what lets
    memory_writer_node record a drill-down edge (Part B3). Returns
    [{"name": str, "parent": str | None}], [] on failure."""
    try:
        from agent.llm import get_llm
        from langchain_core.messages import HumanMessage

        llm = get_llm(temperature=0.0)
        prior_str = ", ".join(prior_topics[:20]) if prior_topics else "(none yet)"
        extraction_prompt = f"""Extract 1-5 specific academic topic names from this conversation turn.

Topics already discussed earlier in this session: {prior_str}

For each extracted topic, if it is a specific subtopic of one of those earlier
topics (a clear drill-down, e.g. "Calvin Cycle" under "Photosynthesis"), set
"parent" to that earlier topic's exact name. Otherwise set "parent" to null.
Only set a parent when confident — when unsure, use null.

Return ONLY a JSON array of objects, nothing else. Example:
[{{"name": "Calvin Cycle", "parent": "Photosynthesis"}}, {{"name": "Mitosis", "parent": null}}]

User prompt: {prompt[:500]}
Assistant response (first 500 chars): {response_text[:500]}"""

        result = await llm.ainvoke([HumanMessage(content=extraction_prompt)])
        text = result.text.strip()
        # Strip markdown code block if present
        if "```" in text:
            text = text.split("```")[1].replace("json", "").strip()
        parsed = json.loads(text)
        out = []
        for item in parsed[:5]:
            if isinstance(item, str):
                out.append({"name": item, "parent": None})
            elif isinstance(item, dict) and isinstance(item.get("name"), str):
                parent = item.get("parent")
                out.append({"name": item["name"], "parent": parent if isinstance(parent, str) and parent in prior_topics else None})
        return out
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


def _upsert_topic_edge(sb, parent_id: str, child_id: str):
    """Part B3: record a drill-down (subtopic) edge between two topics."""
    if parent_id == child_id:
        return
    try:
        sb.table("topic_edges").upsert({
            "parent_id": parent_id,
            "child_id": child_id,
            "relation": "subtopic",
        }, on_conflict="parent_id,child_id").execute()
    except Exception as e:
        logger.warning(f"Topic edge upsert failed for {parent_id} -> {child_id}: {e}")


def _prior_topics_for_session(sb, session_id: str) -> list[str]:
    """Topic names already recorded for this session before this turn.

    Deliberately reads Postgres, not state["topics_touched"]: main.py's
    /api/chat/stream resets topics_touched to [] in the `inputs` dict on
    every single turn (it's not annotated with a reducer, so a fresh
    `inputs` value overwrites whatever the checkpointer persisted), so that
    state field never actually survives across turns. Postgres is the
    durable, correctly session-scoped source for "what did we already touch
    earlier in this session" — needed for the Part B3 drill-down check."""
    try:
        res = (
            sb.table("user_topic_events")
            .select("topics(name)")
            .eq("session_id", session_id)
            .eq("kind", "studied")
            .execute()
        )
        names, seen = [], set()
        for row in res.data or []:
            t = row.get("topics") or {}
            name = t.get("name") if isinstance(t, dict) else None
            if name and name not in seen:
                seen.add(name)
                names.append(name)
        return names
    except Exception as e:
        logger.warning(f"Failed to load prior topics for session {session_id}: {e}")
        return []


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
            ai_msg = msg.text if hasattr(msg, "text") else msg.content
            break
        if hasattr(msg, "role") and getattr(msg, "role", None) == "assistant":
            ai_msg = msg.text if hasattr(msg, "text") else msg.content
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

    # 2. Extract topics (+ drill-down parent, Part B3)
    prior_topics = _prior_topics_for_session(sb, session_id)
    extracted = await _extract_topics_with_parents(prompt, ai_msg, prior_topics)
    topics = [t["name"] for t in extracted]
    topic_ids = {}
    if extracted and user_id:
        for t in extracted:
            tid = _upsert_topic(sb, t["name"])
            if tid:
                topic_ids[t["name"]] = tid
                _record_topic_event(sb, user_id, tid, session_id, "studied")

        # Drill-down edges: parent was touched earlier this session, is a
        # real prior topic (not one just extracted this same turn), and both
        # ids resolved.
        for t in extracted:
            parent_name = t.get("parent")
            if not parent_name or parent_name == t["name"]:
                continue
            child_id = topic_ids.get(t["name"])
            parent_id = topic_ids.get(parent_name) or _upsert_topic(sb, parent_name)
            if child_id and parent_id:
                _upsert_topic_edge(sb, parent_id, child_id)

    # 3. Embed turn and store in Qdrant
    turn_text = f"Q: {prompt}\nA: {ai_msg}"
    if user_id:
        await _embed_and_store(session_id, user_id, topics, turn_text)

    # Return updated topics_touched
    current_topics = state.get("topics_touched", [])
    return {"topics_touched": list(set(current_topics + topics))}
