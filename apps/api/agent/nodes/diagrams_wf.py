from agent.state import AppState
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage
from langfuse.decorators import observe
import uuid
import json
from agent.tools.images import search_images

@observe()
async def diagrams_wf_node(state: AppState):
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.2)
    prompt = state.get("prompt", "")
    
    image_query = f"{prompt} diagram illustration"
    images = search_images(image_query, max_results=3)
    
    system_prompt = f"""You are LearnForge, generating an annotated breakdown for diagrams.
For each image, provide a 2-sentence "easy, simple, accurate" explanation of what it shows.
Return EXACTLY a JSON string inside `<artifact type="diagram_gallery">...</artifact>` tags.
Schema:
<artifact type="diagram_gallery">
{{
  "images": [
    {{
      "url": "image_url",
      "title": "image_title",
      "source_url": "page_url",
      "breakdown": "Your explanation here"
    }}
  ]
}}
</artifact>

IMAGES FOUND:
{json.dumps(images, indent=2)}
"""

    messages = [SystemMessage(content=system_prompt)] + state.get("messages", [])
    response = await llm.ainvoke(messages)
    
    artifacts = state.get("artifacts", [])
    if "<artifact type=\"diagram_gallery\">" in response.content:
        artifacts.append({
            "id": str(uuid.uuid4()),
            "type": "diagram_gallery",
            "content": response.content,
            "created_at": "now"
        })
        
    return {
        "messages": [response],
        "artifacts": artifacts
    }
