import httpx
import logging
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

async def search_wikimedia_images(query: str, max_results: int = 3) -> list:
    """Search Wikimedia Commons for educational images."""
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "prop": "pageimages|imageinfo",
        "generator": "search",
        "gsrsearch": f"{query} diagram OR illustration",
        "gsrlimit": max_results,
        "piprop": "original",
        "iiprop": "url|extmetadata",
    }
    
    results = []
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(url, params=params)
            data = res.json()
            
            pages = data.get("query", {}).get("pages", {})
            for page_id, page in pages.items():
                title = page.get("title", "")
                
                # Get image URL
                img_url = ""
                if "original" in page:
                    img_url = page["original"].get("source", "")
                elif "imageinfo" in page and page["imageinfo"]:
                    img_url = page["imageinfo"][0].get("url", "")
                    
                if not img_url:
                    continue
                    
                # Clean up title
                clean_title = title.replace("File:", "").split(".")[0]
                
                results.append({
                    "title": clean_title,
                    "url": img_url,
                    "source_url": f"https://en.wikipedia.org/?curid={page_id}",
                    "license": "Wikimedia Commons"
                })
    except Exception as e:
        logger.warning(f"Wikimedia search failed: {e}")
        
    return results

async def search_ddg_images(query: str, max_results: int = 3) -> list:
    """Fallback DDG search."""
    try:
        with DDGS() as ddgs:
            raw = list(ddgs.images(query, max_results=max_results))
            return [
                {
                    "title": r.get("title", "Image"),
                    "url": r.get("image"),
                    "source_url": r.get("url"),
                    "license": "Web Search"
                }
                for r in raw if r.get("image")
            ]
    except Exception as e:
        logger.warning(f"DDG Image search failed: {e}")
        return []

async def search_images(query: str, max_results: int = 3) -> list:
    """Pipeline: Wikimedia -> DDG"""
    images = await search_wikimedia_images(query, max_results)
    if len(images) < max_results:
        ddg_imgs = await search_ddg_images(query, max_results - len(images))
        images.extend(ddg_imgs)
    return images[:max_results]
