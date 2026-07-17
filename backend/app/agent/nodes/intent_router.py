import json
import logging
import re
from typing import Any

from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential

from app.agent.state import AgentState
from app.config import get_settings

logger = logging.getLogger(__name__)

VALID_INTENTS = {
    "generate_slides",
    "generate_quiz",
    "generate_notes",
    "generate_diagram",
    "scrape_reference",
    "answer_directly",
}

SCRAPE_HINTS = re.compile(
    r"\b(recent|current|latest|real example|today|this year|up[- ]to[- ]date|news)\b",
    re.IGNORECASE,
)


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            return json.loads(match.group(0))
        raise


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=4))
def _classify_with_groq(user_input: str, user_role: str) -> list[str]:
    settings = get_settings()
    if not settings.groq_api_key:
        return _heuristic_intents(user_input)

    client = Groq(api_key=settings.groq_api_key)
    system = (
        "You classify education content requests into intents. "
        "Return ONLY valid JSON: {\"intents\": [\"...\"]}. "
        f"Allowed intents: {sorted(VALID_INTENTS)}. "
        "Pick one or more intents that apply. "
        "If the user asks for current/recent/latest material, include scrape_reference."
    )
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": f"Role: {user_role}\nRequest: {user_input}"},
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
    )
    raw = completion.choices[0].message.content or "{}"
    data = _extract_json(raw)
    intents = data.get("intents") or data.get("detected_intents") or []
    cleaned = [i for i in intents if i in VALID_INTENTS]
    if not cleaned:
        cleaned = _heuristic_intents(user_input)
    return cleaned


def _heuristic_intents(user_input: str) -> list[str]:
    text = user_input.lower()
    intents: list[str] = []
    if any(w in text for w in ("quiz", "test me", "mcq", "questions")):
        intents.append("generate_quiz")
    if any(w in text for w in ("slide", "deck", "presentation", "powerpoint")):
        intents.append("generate_slides")
    if any(w in text for w in ("diagram", "flowchart", "mermaid", "cycle")):
        intents.append("generate_diagram")
    if any(w in text for w in ("note", "summary", "explain", "re-teach", "reteach", "lesson")):
        intents.append("generate_notes")
    if SCRAPE_HINTS.search(user_input) or "scrape" in text or "reference" in text:
        intents.append("scrape_reference")
    if not intents:
        intents.append("answer_directly")
        intents.append("generate_notes")
    return intents


async def intent_router(state: AgentState) -> dict[str, Any]:
    user_input = state.get("user_input", "")
    user_role = state.get("user_role", "student")
    try:
        intents = _classify_with_groq(user_input, user_role)
    except Exception as exc:
        logger.exception("Intent classification failed, using heuristics: %s", exc)
        intents = _heuristic_intents(user_input)
        errors = list(state.get("errors") or [])
        errors.append(f"intent_router: {exc}")
        return {"detected_intents": intents, "errors": errors, "messages": [{"role": "system", "content": f"intents={intents}"}]}

    if SCRAPE_HINTS.search(user_input) and "scrape_reference" not in intents:
        intents.append("scrape_reference")

    return {
        "detected_intents": intents,
        "messages": [{"role": "system", "content": f"Detected intents: {intents}"}],
    }
