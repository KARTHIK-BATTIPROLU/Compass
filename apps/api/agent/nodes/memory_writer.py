from agent.state import AppState
from langfuse import observe
import os
import logging

logger = logging.getLogger(__name__)

# ── Lazy Supabase client ────────────────────────────────────────────────────
_supabase = None

def get_supabase():
    global _supabase
    if _supabase is None:
        from supabase import create_client
        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_SERVICE_KEY", os.getenv("SUPABASE_ANON_KEY", ""))
        if url and key:
            try:
                _supabase = create_client(url, key)
            except Exception as e:
                logger.warning(f"Supabase client creation failed: {e}")
    return _supabase


@observe()
async def memory_writer_node(state: AppState):
    """
    Saves user + assistant messages to Supabase.
    Non-fatal: if Supabase is down, logs a warning and continues.
    """
    session_id = state.get("session_id")
    prompt = state.get("prompt")
    modes = state.get("modes", [])
    messages = state.get("messages", [])

    supabase = get_supabase()
    if not supabase or not session_id:
        return {}

    # Find the last assistant message (the one just generated)
    ai_msg = None
    for msg in reversed(messages):
        if hasattr(msg, "type") and msg.type == "ai":
            ai_msg = msg.content
            break
        if hasattr(msg, "role") and msg.role == "assistant":
            ai_msg = msg.content
            break

    try:
        rows = [
            {
                "session_id": session_id,
                "role": "user",
                "content": prompt,
                "modes": modes,
            }
        ]
        if ai_msg:
            rows.append(
                {
                    "session_id": session_id,
                    "role": "assistant",
                    "content": ai_msg,
                    "modes": modes,
                }
            )
        supabase.table("messages").insert(rows).execute()
    except Exception as e:
        logger.warning(f"memory_writer: failed to save messages: {e}")

    return {}
