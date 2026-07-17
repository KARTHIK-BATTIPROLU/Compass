from agent.state import AppState
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from langfuse.decorators import observe

@observe()
async def detailed_wf_node(state: AppState):
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.2)
    
    user = state.get("user", {})
    role = user.get("role", "learner")
    class_level = state.get("class_level", "")
    
    system_prompt = f"""You are LearnForge, an advanced AI learning assistant. 
The user is a {role}. Context: {class_level}.
Provide a highly detailed, step-by-step, structured explanation for the user's queries."""

    messages = [SystemMessage(content=system_prompt)] + state.get("messages", [])
    
    response = await llm.ainvoke(messages)
    
    return {"messages": [response]}
