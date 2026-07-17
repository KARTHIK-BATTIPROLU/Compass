import json
import logging
import re
from typing import Any, Optional

from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.db.schemas import QuizPayload, QuizQuestion

logger = logging.getLogger(__name__)


def _strip_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    match = re.search(r"\{[\s\S]*\}", text)
    return match.group(0) if match else text


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=4))
def generate_quiz(
    topic: str,
    n: int = 5,
    grounding: Optional[str] = None,
    strategy: Optional[str] = None,
) -> QuizPayload:
    settings = get_settings()
    grounding_block = ""
    if grounding:
        grounding_block = (
            "\nGround your questions in this reference material when possible:\n"
            f"{grounding[:6000]}\n"
            "Prefer the reference material over assumptions. "
            "If you must use general knowledge, note it.\n"
        )
    strategy_block = ""
    if strategy:
        strategy_block = f"\nUse a {strategy} approach for question framing.\n"

    if not settings.groq_api_key:
        return _fallback_quiz(topic, n)

    client = Groq(api_key=settings.groq_api_key)
    prompt = (
        f"Generate {n} quiz questions on: {topic}. "
        "Mix multiple-choice (with 4 options) and short-answer. "
        'Return ONLY JSON: {"topic": "...", "questions": [{"question": "...", "options": [...], '
        '"correct_answer": "...", "difficulty": "easy|medium|hard", "question_type": "mcq|short_answer"}]}.'
        f"{grounding_block}{strategy_block}"
    )
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are an expert education quiz writer. Output valid JSON only."},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.4,
    )
    raw = _strip_json(completion.choices[0].message.content or "{}")
    data = json.loads(raw)
    return QuizPayload.model_validate(data)


def _fallback_quiz(topic: str, n: int) -> QuizPayload:
    questions = []
    for i in range(n):
        questions.append(
            QuizQuestion(
                question=f"[{topic}] Sample question {i + 1}: What is a key idea about {topic}?",
                options=[
                    f"Concept A related to {topic}",
                    f"Concept B related to {topic}",
                    f"Concept C related to {topic}",
                    "None of the above",
                ],
                correct_answer=f"Concept A related to {topic}",
                difficulty="medium",
                question_type="mcq",
            )
        )
    return QuizPayload(topic=topic, questions=questions)
