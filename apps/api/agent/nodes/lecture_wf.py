from agent.state import AppState
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage
from langfuse.decorators import observe
import uuid

@observe()
async def lecture_wf_node(state: AppState):
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.2)
    
    curriculum_ctx = state.get("curriculum_ctx", [])
    ctx_str = "\n\n".join([f"Topic: {c['metadata'].get('topic', 'N/A')}\n{c['content']}" for c in curriculum_ctx])
    
    system_prompt = f"""You are LearnForge, an AI learning assistant for Faculty.
You must generate a structured 3-part Lecture Script based on the user's prompt and the curriculum context.
Your output MUST be enclosed exactly in `<artifact type="script">` and `</artifact>` tags so the frontend can render it beautifully.
Inside the artifact tag, format the content cleanly using markdown headers exactly like this:
## 1. Introduction
[Content]
## 2. Body
[Content]
## 3. Quiz
[1-2 questions for the learner to pass]

CURRICULUM CONTEXT:
{ctx_str if ctx_str else "No specific curriculum chunks found."}
"""

    messages = [SystemMessage(content=system_prompt)] + state.get("messages", [])
    
    response = await llm.ainvoke(messages)
    
    artifacts = state.get("artifacts", [])
    lecture_flow = state.get("lecture_flow", {})
    
    if "<artifact type=\"script\">" in response.content:
        artifacts.append({
            "id": str(uuid.uuid4()),
            "type": "script",
            "content": response.content,
            "created_at": "now"
        })
        lecture_flow = {
            "active_lesson": True,
            "current_stage": "Intro"
        }
        
    return {
        "messages": [response],
        "artifacts": artifacts,
        "lecture_flow": lecture_flow
    }
