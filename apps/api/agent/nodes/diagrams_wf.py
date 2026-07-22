from agent.state import AppState
from agent.llm import get_llm
from agent.prompt_utils import trim_history
from agent.artifact_parser import extract_artifact, generate_fallback_notice
from langchain_core.messages import SystemMessage, HumanMessage
from langfuse import observe
import uuid
import json
import httpx
import base64
from agent.tools.images import search_images
import logging

logger = logging.getLogger(__name__)

async def fetch_image_b64(url: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(url)
            res.raise_for_status()
            return base64.b64encode(res.content).decode("utf-8")
    except Exception as e:
        logger.warning(f"Failed to fetch image {url}: {e}")
        return ""

@observe()
async def diagrams_wf_node(state: AppState):
    llm = get_llm(temperature=0.2)
    prompt = state.get("prompt", "")
    
    # 1. Search for images
    image_query = f"{prompt} diagram illustration"
    images = await search_images(image_query, max_results=3)
    
    if not images:
        return {"messages": []}

    # 2. Build multi-modal prompt
    content_blocks = [
        {"type": "text", "text": f"""You are LearnForge. I have retrieved the following educational diagrams for the topic: '{prompt}'.
For each image, provide a 2-sentence "easy, simple, accurate" explanation of what it shows.
Return EXACTLY a raw JSON string. Do not use wrapper tags.
Schema:
{{
  "images": [
    {{
      "url": "image_url (provided below)",
      "title": "image_title (provided below)",
      "source_url": "page_url (provided below)",
      "breakdown": "Your explanation here"
    }}
  ]
}}

IMAGES TO ANALYZE:
"""}
    ]

    for img in images:
        b64 = await fetch_image_b64(img["url"])
        content_blocks.append({"type": "text", "text": f"\nImage Title: {img['title']}\nURL: {img['url']}\nSource: {img['source_url']}"})
        if b64:
            content_blocks.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
            })

    messages = trim_history(state.get("messages", [])) + [HumanMessage(content=content_blocks)]
    response = await llm.ainvoke(messages)
    
    artifacts = state.get("artifacts", [])
    response_text = response.text
    
    wrapped_content, tag_present, degraded = extract_artifact(
        response_text, "diagram_gallery", is_json_only=True, workflow_name="diagrams_wf"
    )
    
    if wrapped_content and not degraded:
        response.content = wrapped_content
        artifacts.append({
            "id": str(uuid.uuid4()),
            "type": "diagram_gallery",
            "content": wrapped_content,
            "created_at": "now"
        })
    else:
        response.content = response_text + generate_fallback_notice()
        
    return {
        "messages": [response],
        "artifacts": artifacts
    }

