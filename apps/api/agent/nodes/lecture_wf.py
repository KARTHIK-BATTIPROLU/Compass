from agent.state import AppState
from agent.llm import get_llm
from agent.prompt_utils import trim_history
from agent.artifact_parser import extract_json_payload, generate_fallback_notice
from langchain_core.messages import SystemMessage, AIMessage
from langfuse import observe
import uuid
import logging

logger = logging.getLogger(__name__)

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

Generate a STRUCTURED LECTURE FLOW.
Format your output EXACTLY as a raw JSON string. Do not use wrapper tags.
Schema:
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
}}"""

    response = await llm.ainvoke([SystemMessage(content=system_prompt)])
    content = response.text

    # Parse the structured JSON from the response
    lecture_flow = extract_json_payload(content)
    artifacts = list(state.get("artifacts", []))

    if not lecture_flow:
        logger.warning(f"[lecture_wf] Failed to extract JSON. Degrading.")
        
        # Fallback structured dict
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
        
        response.content = content + generate_fallback_notice()
    else:
        # Build the beautiful markdown presentation in Python
        md = f"# Lecture Flow: {lecture_flow.get('topic', prompt)}\n\n"
        md += f"## 🎣 Opening Hook\n{lecture_flow.get('hook', '')}\n\n"
        md += "## 📚 Segments\n"
        for s in lecture_flow.get('segments', []):
            md += f"### {s.get('title', '')} ({s.get('timing_minutes', 0)} mins)\n"
            md += f"- **Objective:** {s.get('objective', '')}\n"
            md += f"- **Example:** {s.get('example', '')}\n\n"
        md += f"## 🎯 Close & Recap\n{lecture_flow.get('close', '')}\n"
        
        artifact_content = f'<artifact type="flow">\n{md}\n</artifact>'
        response.content = artifact_content
        
        artifacts.append({
            "id": str(uuid.uuid4()),
            "type": "flow",
            "content": artifact_content,
        })

    return {
        "messages": [response],
        "artifacts": artifacts,
        "lecture_flow": lecture_flow,
    }

