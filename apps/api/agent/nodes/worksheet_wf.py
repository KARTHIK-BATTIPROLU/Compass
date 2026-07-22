from agent.state import AppState
from agent.llm import get_llm
from agent.prompt_utils import trim_history, summary_preamble
from agent.artifact_parser import extract_artifact, generate_fallback_notice
from langchain_core.messages import SystemMessage
from langfuse import observe
import uuid
import logging

logger = logging.getLogger(__name__)

@observe()
async def worksheet_wf_node(state: AppState):
    llm = get_llm(temperature=0.2)
    class_level = state.get("class_level", "General")

    system_prompt = f"""You are LearnForge, generating a Worksheet.
Level: {class_level}
Generate a printable worksheet with problems and an answer key based on the user's prompt.
Enclose the output in `<artifact type="worksheet">` and `</artifact>`.
Inside, use markdown. Provide a "## Student Worksheet" section with questions and space, then a "## Answer Key" section.
{summary_preamble(state.get("session_summary"))}"""

    messages = [SystemMessage(content=system_prompt)] + trim_history(state.get("messages", []))
    response = await llm.ainvoke(messages)
    
    artifacts = state.get("artifacts", [])
    response_text = response.text
    
    wrapped_content, tag_present, degraded = extract_artifact(
        response_text, "worksheet", is_json_only=False, workflow_name="worksheet_wf"
    )
    
    if degraded:
        wrapped_content += generate_fallback_notice()
        
    response.content = wrapped_content
    artifacts.append({
        "id": str(uuid.uuid4()),
        "type": "worksheet",
        "content": wrapped_content,
        "created_at": "now"
    })
        
    return {
        "messages": [response],
        "artifacts": artifacts
    }

