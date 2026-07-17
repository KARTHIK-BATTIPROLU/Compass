import asyncio
import logging
import re
from typing import Any
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

from app.agent.state import AgentState

logger = logging.getLogger(__name__)

SCRAPE_TIMEOUT_SECONDS = 25
MAX_SOURCES = 4
PER_URL_TIMEOUT = 10.0

USER_AGENT = (
    "Mozilla/5.0 (compatible; CompassEdTech/1.0; +https://localhost; educational research)"
)


def _extract_topic(user_input: str) -> str:
    text = user_input.strip()
    text = re.sub(
        r"^(give me|make|create|write|generate|lesson on|notes on|slides on|quiz (me )?on)\s+",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\b(with current examples|recent developments in|latest|recent|current)\b",
        " ",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"\s+", " ", text).strip(" .")
    return text[:80] or "education"


def _html_to_text(html: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "nav", "footer", "aside"]):
        tag.decompose()
    title = (soup.title.string.strip() if soup.title and soup.title.string else "")
    parts: list[str] = []
    for p in soup.find_all(["p", "h1", "h2", "h3", "li"]):
        t = p.get_text(" ", strip=True)
        if t and len(t) > 40:
            parts.append(t)
        if len(parts) >= 14:
            break
    return title, "\n\n".join(parts)[:5000]


async def _fetch_jina(client: httpx.AsyncClient, url: str) -> dict[str, Any]:
    """Use Jina Reader to get clean markdown (handles many blocked origins)."""
    proxy = f"https://r.jina.ai/{url}"
    try:
        resp = await client.get(proxy, timeout=PER_URL_TIMEOUT)
        resp.raise_for_status()
        text = resp.text.strip()
        title = url
        if text.startswith("Title:"):
            first, _, rest = text.partition("\n")
            title = first.replace("Title:", "").strip() or url
            text = rest.strip()
        if not text:
            return {"url": url, "title": title, "markdown": "", "error": "empty jina body"}
        return {"url": url, "title": title, "markdown": text[:5000], "error": None}
    except Exception as exc:
        logger.warning("Jina fetch failed for %s: %s", url, exc)
        return {"url": url, "title": "", "markdown": "", "error": str(exc)}


async def _duckduckgo_links(client: httpx.AsyncClient, topic: str) -> list[str]:
    urls: list[str] = []
    try:
        resp = await client.get(
            "https://duckduckgo.com/html/",
            params={"q": f"{topic} education"},
            timeout=PER_URL_TIMEOUT,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        for a in soup.select("a.result__a"):
            href = a.get("href")
            if href and href.startswith("http"):
                urls.append(href)
            if len(urls) >= MAX_SOURCES:
                break
    except Exception as exc:
        logger.warning("DuckDuckGo discovery failed: %s", exc)

    # Stable educational fallbacks
    q = quote_plus(topic)
    urls.extend(
        [
            f"https://en.wikipedia.org/wiki/{topic.replace(' ', '_')}",
            f"https://www.britannica.com/search?query={q}",
            f"https://edu.gcfglobal.org/en/search/?q={q}",
        ]
    )
    seen: set[str] = set()
    out: list[str] = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out[:MAX_SOURCES]


async def _direct_fetch(client: httpx.AsyncClient, url: str) -> dict[str, Any]:
    try:
        resp = await client.get(url, timeout=PER_URL_TIMEOUT, follow_redirects=True)
        resp.raise_for_status()
        title, body = _html_to_text(resp.text)
        if not body:
            return {"url": url, "title": title, "markdown": "", "error": "empty content"}
        return {"url": url, "title": title or url, "markdown": body, "error": None}
    except Exception as exc:
        return {"url": url, "title": "", "markdown": "", "error": str(exc)}


async def scrape_reference(state: AgentState) -> dict[str, Any]:
    topic = _extract_topic(state.get("user_input", "education"))

    async def _run() -> list[dict[str, Any]]:
        async with httpx.AsyncClient(headers={"User-Agent": USER_AGENT}) as client:
            urls = await _duckduckgo_links(client, topic)
            results: list[dict[str, Any]] = []
            for url in urls:
                # Prefer Jina reader; fall back to direct HTML
                item = await _fetch_jina(client, url)
                if not item.get("markdown"):
                    item = await _direct_fetch(client, url)
                results.append(item)
            return results

    try:
        results = await asyncio.wait_for(_run(), timeout=SCRAPE_TIMEOUT_SECONDS)
    except asyncio.TimeoutError:
        logger.error("Scraper timed out after %ss", SCRAPE_TIMEOUT_SECONDS)
        return {
            "scraped_content": [],
            "errors": list(state.get("errors") or []) + ["scraper_node: timeout"],
            "messages": [{"role": "system", "content": "Scrape timed out"}],
            "used_general_knowledge_fallback": True,
        }

    usable = [r for r in results if r.get("markdown")]
    return {
        "scraped_content": results,
        "used_general_knowledge_fallback": len(usable) == 0,
        "messages": [
            {
                "role": "system",
                "content": f"Scraped {len(usable)}/{len(results)} sources on '{topic}'",
            }
        ],
    }
