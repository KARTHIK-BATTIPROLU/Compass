from agent.state import AppState
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage
from langfuse.decorators import observe
import uuid

@observe()
async def flashcards_wf_node(state: AppState):
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.2)
    prompt = state.get("prompt", "")
    class_level = state.get("class_level", "General")
    
    system_prompt = f"""You are LearnForge. Generate a set of 5 flashcards for {class_level} level based on the topic.
Format your output EXACTLY as a JSON string inside `<artifact type="flashcards">...</artifact>`.
Schema:
<artifact type="flashcards">
{{
  "title": "Topic Name",
  "cards": [
    {{
      "front": "Question?",
      "back": "Answer."
    }}
  ]
}}
</artifact>
"""

    messages = [SystemMessage(content=system_prompt)] + state.get("messages", [])
    response = await llm.ainvoke(messages)
    
    artifacts = state.get("artifacts", [])
    if "<artifact type=\"flashcards\">" in response.content:
        artifacts.append({
            "id": str(uuid.uuid4()),
            "type": "flashcards",
            "content": response.content,
            "created_at": "now"
        })
        
    return {
        "messages": [response],
        "artifacts": artifacts
    }
