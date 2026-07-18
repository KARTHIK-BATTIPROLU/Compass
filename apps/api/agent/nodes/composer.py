import uuid
import logging
from agent.state import AppState
from langfuse import observe

from agent.auth import get_supabase

logger = logging.getLogger(__name__)

DEFAULT_FORMATS = {
    "slides": "pptx",
    "script": "docx",
    "worksheet": "docx",
    "flashcards": "csv",
    "research_brief": "pdf",
    "resource_card": "pdf"
}

@observe()
async def composer_node(state: AppState) -> dict:
    """
    Final node in every turn. Collects all artifacts produced this turn,
    ensures each has a stable id, attaches citations, and returns them in
    a structured format that main.py forwards as SSE artifact events.
    """
    artifacts = state.get("artifacts", [])
    citations = state.get("citations", [])
    session_id = state.get("session_id")
    
    sb = get_supabase()

    normalized = []
    for art in artifacts:
        # Ensure stable id
        art_id = art.get("id") or str(uuid.uuid4())
        art_type = art.get("type", "unknown")
        
        # Attach download_url
        default_fmt = DEFAULT_FORMATS.get(art_type, "docx")
        download_url = f"/api/artifacts/{art_id}/export?format={default_fmt}"
        
        norm_art = {
            **art,
            "id": art_id,
            "download_url": download_url
        }
        
        # Persist to Supabase non-fatally. upsert (not insert): some workflow
        # nodes (e.g. quiz_wf) already persist their own artifacts row earlier
        # in the turn to satisfy a downstream FK, so this is often an update.
        if sb and session_id:
            try:
                sb.table("artifacts").upsert({
                    "id": art_id,
                    "session_id": session_id,
                    "type": art_type,
                    "content_md": norm_art.get("content", ""),
                    "export_urls": {"default": download_url}
                }, on_conflict="id").execute()
            except Exception as e:
                logger.warning(f"Failed to persist artifact {art_id}: {e}")
                
        normalized.append(norm_art)

    if normalized:
        logger.info(f"composer: emitting {len(normalized)} artifact(s): {[a['type'] for a in normalized]}")

    return {
        "artifacts": normalized,
        "citations": citations,
    }
