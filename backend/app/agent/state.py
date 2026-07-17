from typing import Any, Optional, TypedDict


class AgentState(TypedDict, total=False):
    user_input: str
    user_id: str
    user_role: str
    detected_intents: list[str]
    generated_content: dict[str, Any]
    scraped_content: list[dict[str, Any]]
    needs_human_review: bool
    review_status: str  # pending | approved | edited | regenerated
    thread_id: str
    messages: list[dict[str, Any]]
    weak_spot_context: Optional[dict[str, Any]]
    force_reexplain_strategy: Optional[str]
    regenerate_target: Optional[str]
    regenerate_instruction: Optional[str]
    errors: list[str]
    used_general_knowledge_fallback: bool
