from agent.state import AppState
from agent.llm import get_llm
from langchain_core.messages import SystemMessage, AIMessage
from langfuse import observe
import uuid
import json

@observe()
async def lecture_wf_node(state: AppState):
    """
    Lecture Flow workflow.
    Generates: opening hook → segments (objective + example + timing) → close/recap.
    Sets state["lecture_flow"] to a structured dict so was_wf gate can read it.
    """
    llm = get_llm(temperature=0.2)

    prompt = state.get("prompt", "")
    curriculum_ctx = state.get("curriculum_ctx", [])
    class_level = state.get("class_level", "general")

    ctx_str = "\n\n".join(
        [f"Topic: {c['metadata'].get('topic', 'N/A')}\n{c['content']}" for c in curriculum_ctx]
    )

    system_prompt = f"""You are LearnForge, an AI teaching assistant helping faculty plan a lesson.

Topic: {prompt}
Class Level: {class_level}

CURRICULUM CONTEXT:
{ctx_str if ctx_str else "No specific curriculum chunks available."}

Generate a STRUCTURED LECTURE FLOW. Output BOTH:

1. A JSON structure (inside <flow_json> tags) that the system will use to gate W-A-S:
<flow_json>
{{
  "topic": "<topic name>",
  "class_level": "<level>",
  "hook": "<opening hook — 1-2 sentences that grab attention>",
  "segments": [
    {{
      "title": "<segment name>",
      "objective": "<what students will understand after this segment>",
      "example": "<concrete example or analogy>",
      "timing_minutes": <number>
    }}
  ],
  "close": "<closing recap — 1-2 sentences summarizing key takeaways>"
}}
</flow_json>

2. A beautiful markdown presentation (inside <artifact type="flow"> tags):
<artifact type="flow">
# Lecture Flow: {prompt}

## 🎣 Opening Hook
[Hook content]

## 📚 Segments
[For each segment: title, objective, example, timing]

## 🎯 Close & Recap
[Closing content]
</artifact>"""

    response = await llm.ainvoke([SystemMessage(content=system_prompt)])
    content = response.text

    # Parse the structured JSON from the response
    lecture_flow = None
    try:
        import re
        json_match = re.search(r"<flow_json>(.*?)</flow_json>", content, re.DOTALL)
        if json_match:
            lecture_flow = json.loads(json_match.group(1).strip())
    except Exception as e:
        # Fallback structured dict if JSON parse fails
        lecture_flow = {
            "topic": prompt,
            "class_level": class_level,
            "hook": "Engaging opening for this lesson.",
            "segments": [
                {
                    "title": "Introduction",
                    "objective": "Understand the basics",
                    "example": "See content above",
                    "timing_minutes": 10,
                }
            ],
            "close": "Summary and key takeaways.",
        }

    artifacts = list(state.get("artifacts", []))
    artifacts.append({
        "id": str(uuid.uuid4()),
        "type": "flow",
        "content": content,
    })

    return {
        "messages": [AIMessage(content=content)],
        "artifacts": artifacts,
        "lecture_flow": lecture_flow,
    }
