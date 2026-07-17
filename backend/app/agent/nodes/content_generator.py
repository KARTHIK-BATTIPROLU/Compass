import asyncio
import logging
from typing import Any, Optional

from app.agent.state import AgentState
from app.agent.tools.diagram_tool import generate_diagram
from app.agent.tools.notes_tool import generate_notes
from app.agent.tools.quiz_tool import generate_quiz
from app.agent.tools.slides_tool import generate_slides

logger = logging.getLogger(__name__)


def _grounding_text(state: AgentState) -> Optional[str]:
    sources = state.get("scraped_content") or []
    parts = []
    for s in sources:
        if s.get("markdown"):
            parts.append(f"### {s.get('title') or s.get('url')}\nSource: {s.get('url')}\n{s['markdown']}")
    return "\n\n".join(parts) if parts else None


async def content_generator(state: AgentState) -> dict[str, Any]:
    intents = state.get("detected_intents") or []
    topic = state.get("user_input", "")
    grounding = _grounding_text(state)
    strategy = state.get("force_reexplain_strategy")
    regenerate_target = state.get("regenerate_target")
    reject_note = state.get("regenerate_instruction")
    errors = list(state.get("errors") or [])
    content: dict[str, Any] = dict(state.get("generated_content") or {})

    async def _quiz():
        return await asyncio.to_thread(generate_quiz, topic, 5, grounding, strategy)

    async def _slides():
        return await asyncio.to_thread(generate_slides, topic, grounding, strategy, reject_note)

    async def _diagram():
        return await asyncio.to_thread(generate_diagram, topic, grounding, reject_note)

    async def _notes():
        return await asyncio.to_thread(generate_notes, topic, grounding, strategy, reject_note)

    async def _answer():
        notes = await _notes()
        return notes

    tasks: dict[str, Any] = {}
    if regenerate_target:
        mapping = {
            "quiz": ("quiz", _quiz),
            "slides": ("slides", _slides),
            "diagram": ("diagram", _diagram),
            "notes": ("notes", _notes),
        }
        if regenerate_target in mapping:
            key, fn = mapping[regenerate_target]
            tasks[key] = fn()
    else:
        if "generate_quiz" in intents:
            tasks["quiz"] = _quiz()
        if "generate_slides" in intents:
            tasks["slides"] = _slides()
        if "generate_diagram" in intents:
            tasks["diagram"] = _diagram()
        if "generate_notes" in intents or "answer_directly" in intents:
            tasks["notes"] = _notes() if "generate_notes" in intents else _answer()

    if not tasks:
        tasks["notes"] = _notes()

    keys = list(tasks.keys())
    results = await asyncio.gather(*tasks.values(), return_exceptions=True)
    for key, result in zip(keys, results):
        if isinstance(result, Exception):
            logger.exception("Generator %s failed: %s", key, result)
            errors.append(f"content_generator.{key}: {result}")
            content[key] = {"error": str(result)}
        else:
            content[key] = result.model_dump() if hasattr(result, "model_dump") else result

    if grounding:
        content["grounding_used"] = True
        content["sources"] = [
            {"url": s.get("url"), "title": s.get("title"), "error": s.get("error")}
            for s in (state.get("scraped_content") or [])
        ]
    else:
        content["grounding_used"] = False

    return {
        "generated_content": content,
        "needs_human_review": True,
        "review_status": "pending",
        "errors": errors,
        "messages": [{"role": "system", "content": f"Generated: {list(content.keys())}"}],
    }
