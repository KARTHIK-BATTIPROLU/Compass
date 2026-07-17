import logging
from typing import Any, Optional

from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.db.schemas import NotesPayload

logger = logging.getLogger(__name__)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=4))
def generate_notes(
    topic: str,
    grounding: Optional[str] = None,
    strategy: Optional[str] = None,
    reject_note: Optional[str] = None,
) -> NotesPayload:
    settings = get_settings()
    strategy = strategy or "text-based"
    if not settings.groq_api_key:
        return NotesPayload(
            topic=topic,
            title=f"Notes: {topic}",
            body=f"Overview of {topic}.\n\n1. Core idea\n2. Example\n3. Practice tip",
            strategy=strategy,
        )

    grounding_block = ""
    if grounding:
        grounding_block = (
            f"\nGround in this material:\n{grounding[:6000]}\n"
            "Prefer references over assumptions.\n"
        )
    strategy_instruction = {
        "text-based": "Use clear textual exposition with definitions.",
        "example-based": "Lead with concrete worked examples.",
        "visual-based": "Describe visual models and spatial relationships.",
        "analogy-based": "Teach primarily through vivid analogies and metaphors.",
    }.get(strategy, f"Use a {strategy} approach.")

    reject_block = f"\n{reject_note}\n" if reject_note else ""
    client = Groq(api_key=settings.groq_api_key)
    prompt = (
        f"Write concise study notes on: {topic}.\n"
        f"Strategy: {strategy_instruction}\n"
        "Return plain markdown notes, not JSON."
        f"{grounding_block}{reject_block}"
    )
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are an expert tutor writing study notes."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.5,
    )
    body = completion.choices[0].message.content or ""
    return NotesPayload(topic=topic, title=f"Notes: {topic}", body=body, strategy=strategy)
