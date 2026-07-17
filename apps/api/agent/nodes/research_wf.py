from agent.state import AppState
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage
from langfuse import observe
import uuid
from agent.tools.search import search_web, search_arxiv

@observe()
async def research_wf_node(state: AppState):
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.2)
    prompt = state.get("prompt", "")
    class_level = state.get("class_level", "General")
    
    web_results = await search_web(prompt)
    arxiv_results = await search_arxiv(prompt)
    
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
"""

    messages = [SystemMessage(content=system_prompt)] + state.get("messages", [])
    response = await llm.ainvoke(messages)
    
    artifacts = state.get("artifacts", [])
    if "<artifact type=\"research_brief\">" in response.content:
        artifacts.append({
            "id": str(uuid.uuid4()),
            "type": "research_brief",
            "content": response.content,
            "created_at": "now"
        })
        
    return {
        "messages": [response],
        "artifacts": artifacts
    }
