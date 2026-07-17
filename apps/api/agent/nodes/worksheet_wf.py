from agent.state import AppState
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage
from langfuse import observe
import uuid

@observe()
async def worksheet_wf_node(state: AppState):
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.2)
    class_level = state.get("class_level", "General")
    
    system_prompt = f"""You are LearnForge, generating a Worksheet.
Level: {class_level}
Generate a printable worksheet with problems and an answer key based on the user's prompt.
Enclose the output in `<artifact type="worksheet">` and `</artifact>`.
Inside, use markdown. Provide a "## Student Worksheet" section with questions and space, then a "## Answer Key" section.
"""

    messages = [SystemMessage(content=system_prompt)] + state.get("messages", [])
    response = await llm.ainvoke(messages)
    
    artifacts = state.get("artifacts", [])
    if "<artifact type=\"worksheet\">" in response.content:
        artifacts.append({
            "id": str(uuid.uuid4()),
            "type": "worksheet",
            "content": response.content,
            "created_at": "now"
        })
        
    return {
        "messages": [response],
        "artifacts": artifacts
    }
