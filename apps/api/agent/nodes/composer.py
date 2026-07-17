import uuid
import logging
from agent.state import AppState
from langfuse import observe

logger = logging.getLogger(__name__)

@observe()
async def composer_node(state: AppState) -> dict:
    """
    Final node in every turn. Collects all artifacts produced this turn,
    ensures each has a stable id, attaches citations, and returns them in
    a structured format that main.py forwards as SSE artifact events.
    """
    artifacts = state.get("artifacts", [])
    citations = state.get("citations", [])

    # Ensure every artifact has a stable id
    normalized = []
    for art in artifacts:
        if not art.get("id"):
            art = {**art, "id": str(uuid.uuid4())}
        normalized.append(art)

    if normalized:
        logger.info(f"composer: emitting {len(normalized)} artifact(s): {[a['type'] for a in normalized]}")

    return {
        "artifacts": normalized,
        "citations": citations,
    }
