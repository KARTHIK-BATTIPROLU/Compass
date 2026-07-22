from agent.state import AppState
from agent.llm import get_llm
from agent.prompt_utils import trim_history, summary_preamble
from agent.artifact_parser import extract_artifact, generate_fallback_notice
from langchain_core.messages import SystemMessage
from langfuse import observe
import uuid
import logging
from agent.tools.search import search_web, search_arxiv, search_semantic_scholar

logger = logging.getLogger(__name__)

@observe()
async def research_wf_node(state: AppState):
    llm = get_llm(temperature=0.2)
    prompt = state.get("prompt", "")
    class_level = state.get("class_level", "General")
    
    web_results = await search_web(prompt)
    arxiv_results = await search_arxiv(prompt)
    scholar_results = await search_semantic_scholar(prompt)
    
    system_prompt = f"""You are LearnForge, generating an 'Update & Research' brief for a Faculty member teaching {class_level}.
Using the provided sources, generate a relevance-ranked brief summarizing recent developments and specifically including a "Why this matters for your class" section.
Include citations (e.g. [1], [2]) inline.

Format your entire output exactly as a JSON string within `<artifact type="research_brief">...</artifact>` like this:
<artifact type="research_brief">
{{
  "title": "Brief Title",
  "brief_markdown": "Markdown formatted brief text with inline citations...",
  "citations": [
    {{"id": "1", "title": "Source Title", "url": "https://..."}}
  ]
}}
</artifact>

WEB SOURCES:
{web_results}

ARXIV SOURCES:
{arxiv_results}

SEMANTIC SCHOLAR SOURCES:
{scholar_results}
{summary_preamble(state.get("session_summary"))}"""

    messages = [SystemMessage(content=system_prompt)] + trim_history(state.get("messages", []))
    response = await llm.ainvoke(messages)
    
    artifacts = state.get("artifacts", [])
    response_text = response.text
    
    wrapped_content, tag_present, degraded = extract_artifact(
        response_text, "research_brief", is_json_only=False, workflow_name="research_wf"
    )
    
    if degraded:
        wrapped_content += generate_fallback_notice()
        
    response.content = wrapped_content
    artifacts.append({
        "id": str(uuid.uuid4()),
        "type": "research_brief",
        "content": wrapped_content,
        "created_at": "now"
    })
        
    return {
        "messages": [response],
        "artifacts": artifacts
    }

