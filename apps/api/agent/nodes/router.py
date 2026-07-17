from agent.state import AppState
from langfuse import observe

# ── Chip label → route map ──────────────────────────────────────────────────
# Canonical chip labels (from UI) mapped to graph node names.
# Comparison is case-insensitive and strips extra spaces.
CHIP_ROUTES = {
    "lecture flow":        "lecture_wf",
    "lecture script":      "lecture_wf",   # legacy alias
    "w-a-s":               "was_wf",
    "was":                 "was_wf",
    "weak-average-strong": "was_wf",
    "quiz":                "quiz_wf",
    "quiz me":             "quiz_wf",
    "worksheet":           "worksheet_wf",
    "update & research":   "research_wf",
    "research":            "research_wf",
    "resource":            "resource_wf",
    "diagrams":            "diagrams_wf",
    "flashcards":          "flashcards_wf",
    "curriculum":          "curriculum_wf",
    "detailed":            "detailed_wf",
}

@observe()
async def router_node(state: AppState) -> AppState:
    modes = state.get("modes", [])
    modes_lower = [m.strip().lower() for m in modes]

    # Walk chip routes in priority order
    for chip in modes_lower:
        if chip in CHIP_ROUTES:
            return {"route": CHIP_ROUTES[chip]}

    # Default: detailed explanation
    return {"route": "detailed_wf"}
