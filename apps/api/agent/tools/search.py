from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.utilities.arxiv import ArxivAPIWrapper
import os

tavily_tool = TavilySearchResults(max_results=3)
arxiv_wrapper = ArxivAPIWrapper(top_k_results=3, doc_content_chars_max=1000)

async def search_web(query: str):
    if not os.getenv("TAVILY_API_KEY"):
        return [{"title": "Web Search Disabled", "url": "#", "content": "Missing TAVILY_API_KEY"}]
    try:
        results = tavily_tool.invoke({"query": query})
        return results
    except Exception as e:
        print("Tavily search failed:", e)
        return []

async def search_arxiv(query: str):
    try:
        results = arxiv_wrapper.run(query)
        return results
    except Exception as e:
        print("ArXiv search failed:", e)
        return "No results found."
