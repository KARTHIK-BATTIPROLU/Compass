from typing import Any

from langgraph.types import interrupt

from app.agent.state import AgentState


async def human_review_gate(state: AgentState) -> dict[str, Any]:
    """Pause for human approval / edit / regenerate before finalizing."""
    payload = {
        "generated_content": state.get("generated_content") or {},
        "detected_intents": state.get("detected_intents") or [],
        "needs_human_review": True,
    }
    decision = interrupt(payload)
    # decision expected: {action: approve|edit|regenerate, content?, target?, instruction?}
    if not isinstance(decision, dict):
        decision = {"action": "approve"}

    action = decision.get("action", "approve")
    updates: dict[str, Any] = {
        "review_status": action,
        "needs_human_review": action != "approve",
    }
    if action == "edit" and decision.get("content"):
        merged = dict(state.get("generated_content") or {})
        merged.update(decision["content"])
        updates["generated_content"] = merged
        updates["needs_human_review"] = False
        updates["review_status"] = "edited"
    if action == "regenerate":
        updates["regenerate_target"] = decision.get("target")
        updates["regenerate_instruction"] = decision.get(
            "instruction",
            "The user rejected the previous output, try again differently.",
        )
        updates["needs_human_review"] = True
    if action == "approve":
        updates["needs_human_review"] = False
        updates["review_status"] = "approved"
    return updates
