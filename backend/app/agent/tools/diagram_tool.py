import logging
import re
from typing import Optional

from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.db.schemas import DiagramPayload

logger = logging.getLogger(__name__)


def _extract_mermaid(text: str) -> str:
    text = text.strip()
    fence = re.search(r"```(?:mermaid)?\s*([\s\S]*?)```", text)
    if fence:
        return fence.group(1).strip()
    if text.startswith("flowchart") or text.startswith("graph") or text.startswith("sequenceDiagram"):
        return text
    match = re.search(r"(flowchart[\s\S]+|graph[\s\S]+|sequenceDiagram[\s\S]+)", text)
    if match:
        return match.group(1).strip()
    return text


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=4))
def generate_diagram(
    topic: str,
    grounding: Optional[str] = None,
    reject_note: Optional[str] = None,
) -> DiagramPayload:
    settings = get_settings()
    if not settings.groq_api_key and not settings.gemini_api_key:
        return _fallback_diagram(topic)

    grounding_block = f"\nReference context:\n{grounding[:4000]}\n" if grounding else ""
    reject_block = f"\n{reject_note}\n" if reject_note else ""
    prompt = (
        f"Create a Mermaid.js diagram that explains: {topic}. "
        "Return ONLY the Mermaid definition (flowchart preferred). "
        "Use valid Mermaid syntax. No markdown fences if possible."
        f"{grounding_block}{reject_block}"
    )

    if settings.groq_api_key:
        client = Groq(api_key=settings.groq_api_key)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You output valid Mermaid diagram syntax only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        mermaid = _extract_mermaid(completion.choices[0].message.content or "")
    else:
        import google.generativeai as genai

        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        mermaid = _extract_mermaid(response.text or "")

    return DiagramPayload(topic=topic, mermaid=mermaid)


def _fallback_diagram(topic: str) -> DiagramPayload:
    safe = re.sub(r"[^a-zA-Z0-9 ]", "", topic)[:40] or "Topic"
    mermaid = f"""flowchart TD
    A[{safe}] --> B[Key Concept 1]
    A --> C[Key Concept 2]
    B --> D[Example]
    C --> D
    D --> E[Summary]
"""
    return DiagramPayload(topic=topic, mermaid=mermaid)
