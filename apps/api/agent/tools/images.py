from duckduckgo_search import DDGS

def search_images(query: str, max_results: int = 3):
    try:
        with DDGS() as ddgs:
            results = ddgs.images(query, max_results=max_results)
            return list(results)
    except Exception as e:
        print("Image search failed:", e)
        return []
