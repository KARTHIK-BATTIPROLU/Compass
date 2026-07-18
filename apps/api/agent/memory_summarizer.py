"""
memory_summarizer.py — Lazy session summarizer (Final Sprint Part B1).

Trigger: called whenever a session list is fetched (routers/memory.py
`GET /api/memory/sessions`), not on a timer — the spec's "lightweight
approach" of summarizing lazily on next listing rather than running a
background job on close/inactivity.

A session becomes eligible once it has >= 4 messages and has no summary
yet. Eligible sessions get a 2-3 sentence Gemini summary saved to
`sessions.summary` and embedded into Qdrant `session_chunks` so it's
retrievable via search_my_history too. Non-fatal: any failure logs a
warning and the session is simply skipped (summary stays null, retried
next listing).
"""
import logging
from typing import Optional

from langchain_core.messages import HumanMessage

from agent.nodes.memory_writer import get_embeddings, get_qdrant

logger = logging.getLogger(__name__)

MIN_MESSAGES = 4


async def _embed_summary(session_id: str, user_id: str, summary: str) -> None:
    emb = get_embeddings()
    qdrant = get_qdrant()
    if not emb or not qdrant:
        return
    try:
        import uuid
        from qdrant_client.models import PointStruct

        vector = await emb.aembed_query(summary)
        qdrant.upsert(
            collection_name="session_chunks",
            points=[PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "session_id": session_id,
                    "user_id": user_id,
                    "topics": [],
                    "text": summary,
                    "kind": "session_summary",
                },
            )],
        )
    except Exception as e:
        logger.warning(f"Failed to embed session summary for {session_id}: {e}")


async def maybe_summarize_session(sb, session_id: str, user_id: str, existing_summary: Optional[str]) -> Optional[str]:
    """Returns the session's summary, generating and persisting one if the
    session just became eligible (>=4 messages, no summary yet). Returns
    None if not yet eligible and no summary exists."""
    if existing_summary:
        return existing_summary

    try:
        msgs_res = (
            sb.table("messages")
            .select("role, content")
            .eq("session_id", session_id)
            .order("created_at")
            .execute()
        )
        messages = msgs_res.data or []
    except Exception as e:
        logger.warning(f"Failed to load messages for summarizer, session {session_id}: {e}")
        return None

    if len(messages) < MIN_MESSAGES:
        return None

    transcript = "\n".join(f"{m['role']}: {m['content']}" for m in messages if m.get("content"))[:6000]
    if not transcript.strip():
        return None

    try:
        from agent.llm import get_llm

        llm = get_llm(temperature=0.2)
        prompt = (
            "Summarize this tutoring conversation in exactly 2-3 sentences, "
            "focused on what topics were covered and what was learned. "
            "Write it as a plain description, no preamble, no markdown.\n\n"
            f"{transcript}"
        )
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        summary = response.text.strip()
        if not summary:
            return None
    except Exception as e:
        logger.warning(f"Summary generation failed for session {session_id}: {e}")
        return None

    try:
        sb.table("sessions").update({"summary": summary}).eq("id", session_id).execute()
    except Exception as e:
        logger.warning(f"Failed to save summary for session {session_id}: {e}")

    await _embed_summary(session_id, user_id, summary)

    return summary
