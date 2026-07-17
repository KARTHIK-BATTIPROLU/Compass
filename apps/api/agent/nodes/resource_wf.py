from agent.state import AppState
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage
from langfuse.decorators import observe
import uuid
from agent.tools.search import search_web, search_arxiv

@observe()
async def resource_wf_node(state: AppState):
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.2)
    prompt = state.get("prompt", "")
    
    web_results = await search_web(f"news {prompt}")
    arxiv_results = await search_arxiv(prompt)
    
    system_prompt = f"""You are LearnForge, generating a Resource Card for a Learner.
Synthesize the sources into an easy-to-understand summary.
Format your entire output exactly as a JSON string within `<artifact type="resource_card">...</artifact>` like this:
<artifact type="resource_card">
{{
  "synthesis_markdown": "Markdown text with inline citations [1]...",
  "news": [{{"title": "...", "url": "..."}}],
  "papers": [{{"title": "...", "url": "..."}}],
  "docs": [{{"title": "...", "url": "..."}}],
  "citations": [{{"id": "1", "title": "Source Title", "url": "https://..."}}]
}}
</artifact>

Map web sources to "news" or "docs" based on your judgment. Map arxiv sources to "papers". If a category has no items, use an empty list.

WEB SOURCES:
{web_results}

ARXIV SOURCES:
{arxiv_results}
"""

    messages = [SystemMessage(content=system_prompt)] + state.get("messages", [])
    response = await llm.ainvoke(messages)
    
    artifacts = state.get("artifacts", [])
    if "<artifact type=\"resource_card\">" in response.content:
        artifacts.append({
            "id": str(uuid.uuid4()),
            "type": "resource_card",
            "content": response.content,
            "created_at": "now"
        })
        
    return {
        "messages": [response],
        "artifacts": artifacts
    }
