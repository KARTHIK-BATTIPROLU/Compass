import json
import logging
import re
from typing import Optional

from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.db.schemas import Slide, SlidesPayload

logger = logging.getLogger(__name__)


def _strip_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    match = re.search(r"\{[\s\S]*\}", text)
    return match.group(0) if match else text


def _build_prompt(
    topic: str,
    grounding: Optional[str],
    strategy: Optional[str],
    reject_note: Optional[str],
) -> str:
    grounding_block = ""
    if grounding:
        grounding_block = (
            "\nUse this reference material as primary grounding:\n"
            f"{grounding[:8000]}\n"
            "Prefer scraped specifics over general knowledge.\n"
        )
    strategy_block = f"\nExplanation strategy: {strategy}\n" if strategy else ""
    reject_block = f"\n{reject_note}\n" if reject_note else ""
    return (
        f"Create a structured slide deck on: {topic}. "
        "Return ONLY JSON with shape: "
        '{"topic": "...", "slides": [{"title": "...", "bullet_points": ["..."], '
        '"speaker_notes": "...", "visual_suggestion": "..."}]} '
        "Aim for 5-8 slides."
        f"{grounding_block}{strategy_block}{reject_block}"
    )


def _via_gemini(prompt: str) -> SlidesPayload:
    import google.generativeai as genai

    settings = get_settings()
    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    raw = _strip_json(response.text or "{}")
    return SlidesPayload.model_validate(json.loads(raw))


def _via_groq(prompt: str) -> SlidesPayload:
    from groq import Groq

    settings = get_settings()
    client = Groq(api_key=settings.groq_api_key)
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are an expert instructional designer. Output valid JSON only."},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.4,
    )
    raw = _strip_json(completion.choices[0].message.content or "{}")
    return SlidesPayload.model_validate(json.loads(raw))


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=0.5, min=0.5, max=4))
def generate_slides(
    topic: str,
    grounding: Optional[str] = None,
    strategy: Optional[str] = None,
    reject_note: Optional[str] = None,
) -> SlidesPayload:
    settings = get_settings()
    prompt = _build_prompt(topic, grounding, strategy, reject_note)

    if settings.gemini_api_key:
        try:
            return _via_gemini(prompt)
        except Exception as exc:
            logger.warning("Gemini slides failed (%s); trying Groq", exc)

    if settings.groq_api_key:
        try:
            return _via_groq(prompt)
        except Exception as exc:
            logger.warning("Groq slides failed (%s); using static fallback", exc)

    return _fallback_slides(topic)


def _fallback_slides(topic: str) -> SlidesPayload:
    return SlidesPayload(
        topic=topic,
        slides=[
            Slide(
                title=f"Introduction to {topic}",
                bullet_points=[f"Overview of {topic}", "Learning goals", "Why it matters"],
                speaker_notes=f"Introduce {topic} and set expectations.",
                visual_suggestion="Title slide with thematic imagery",
            ),
            Slide(
                title="Key Concepts",
                bullet_points=["Core idea 1", "Core idea 2", "Core idea 3"],
                speaker_notes="Walk through the foundational concepts.",
                visual_suggestion="Concept map",
            ),
            Slide(
                title="Worked Example",
                bullet_points=["Setup", "Steps", "Result"],
                speaker_notes="Demonstrate with a concrete example.",
                visual_suggestion="Step diagram",
            ),
            Slide(
                title="Practice & Summary",
                bullet_points=["Check for understanding", "Common pitfalls", "Next steps"],
                speaker_notes="Recap and assign practice.",
                visual_suggestion="Summary checklist",
            ),
        ],
    )
