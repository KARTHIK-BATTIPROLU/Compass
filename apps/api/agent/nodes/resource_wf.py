from agent.state import AppState
from agent.llm import get_llm
from agent.prompt_utils import trim_history, summary_preamble
from agent.artifact_parser import extract_artifact, generate_fallback_notice
from langchain_core.messages import SystemMessage
from langfuse import observe
import uuid
from agent.tools.search import search_web, search_arxiv, search_semantic_scholar
import logging

logger = logging.getLogger(__name__)

@observe()
async def resource_wf_node(state: AppState):
    llm = get_llm(temperature=0.2)
    prompt = state.get("prompt", "")
    
    web_results = await search_web(f"news {prompt}")
    arxiv_results = await search_arxiv(prompt)
    scholar_results = await search_semantic_scholar(prompt)
    
    system_prompt = f"""You are LearnForge, generating a Resource Card for a Learner.
Synthesize the sources into an easy-to-understand summary.
Format your entire output exactly as a raw JSON string. Do not use wrapper tags.
Schema:
{{
  "synthesis_markdown": "Markdown text with inline citations [1]...",
  "news": [{{"title": "...", "url": "..."}}],
  "papers": [{{"title": "...", "url": "..."}}],
  "docs": [{{"title": "...", "url": "..."}}],
  "citations": [{{"id": "1", "title": "Source Title", "url": "https://..."}}]
}}

Map web sources to "news" or "docs" based on your judgment. Map arxiv sources to "papers". If a category has no items, use an empty list.

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
        response_text, "resource_card", is_json_only=True, workflow_name="resource_wf"
    )
    
    if wrapped_content and not degraded:
        response.content = wrapped_content
        artifacts.append({
            "id": str(uuid.uuid4()),
            "type": "resource_card",
            "content": wrapped_content,
            "created_at": "now"
        })
    else:
        response.content = response_text + generate_fallback_notice()
        
    return {
        "messages": [response],
        "artifacts": artifacts
    }

