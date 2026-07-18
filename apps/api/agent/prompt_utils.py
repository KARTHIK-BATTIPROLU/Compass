"""
prompt_utils.py — shared helpers for trimming what gets sent to the LLM.

Long sessions were degrading (slower, pricier turns) because every node
that reads conversation history appended the FULL, ever-growing message
list to every prompt. trim_history caps that to the most recent turns; the
session summary (Part B1) covers what came before.
"""

MAX_HISTORY_TURNS = 12


def trim_history(messages: list, max_turns: int = MAX_HISTORY_TURNS) -> list:
    """Keep only the most recent `max_turns` conversational turns (a turn is
    a human message + its response, so this keeps up to 2*max_turns
    messages). Cheap and safe: never mutates the input list."""
    max_messages = max_turns * 2
    if len(messages) <= max_messages:
        return messages
    return messages[-max_messages:]


def summary_preamble(session_summary: str | None) -> str:
    """A short system-prompt-ready blurb summarizing everything before the
    trimmed history window, or "" if there's no summary yet."""
    if not session_summary:
        return ""
    return f"\n\nEARLIER IN THIS SESSION (summary): {session_summary}\n"
