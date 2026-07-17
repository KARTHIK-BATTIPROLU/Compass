import os
import logging

logger = logging.getLogger(__name__)

# ── Lazy Tavily ─────────────────────────────────────────────────────────────
_tavily_tool = None

def get_tavily():
    global _tavily_tool
    if _tavily_tool is None and os.getenv("TAVILY_API_KEY"):
        try:
            from langchain_community.tools.tavily_search import TavilySearchResults
            _tavily_tool = TavilySearchResults(max_results=5)
        except Exception as e:
            logger.warning(f"Tavily init failed: {e}")
    return _tavily_tool


# ── Lazy ArXiv ───────────────────────────────────────────────────────────────
_arxiv_wrapper = None

def get_arxiv():
    global _arxiv_wrapper
    if _arxiv_wrapper is None:
        try:
            from langchain_community.utilities.arxiv import ArxivAPIWrapper
            _arxiv_wrapper = ArxivAPIWrapper(top_k_results=5, doc_content_chars_max=1500)
        except Exception as e:
            logger.warning(f"ArXiv init failed: {e}")
    return _arxiv_wrapper


async def search_web(query: str) -> list:
    """Search web using Tavily. Returns fallback if key missing."""
    tool = get_tavily()
    if not tool:
        return [{"title": "Web Search Unavailable", "url": "#", "content": "TAVILY_API_KEY not configured — add it to apps/api/.env"}]
    try:
        results = tool.invoke({"query": query})
        return results if isinstance(results, list) else []
    except Exception as e:
        logger.warning(f"Tavily search failed for '{query}': {e}")
        return []


async def search_arxiv(query: str) -> str:
    """Search arXiv for academic papers. Returns empty string on failure."""
    wrapper = get_arxiv()
    if not wrapper:
        return "arXiv search unavailable."
    try:
        return wrapper.run(query)
    except Exception as e:
        logger.warning(f"arXiv search failed for '{query}': {e}")
        return "No arXiv results found."
