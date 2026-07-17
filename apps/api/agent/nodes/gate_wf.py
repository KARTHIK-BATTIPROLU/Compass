from agent.state import AppState
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage
from langfuse.decorators import observe

@observe()
async def gate_wf_node(state: AppState):
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.1)
    lecture_flow = state.get("lecture_flow", {})
    
    # Simple gating mock
    system_prompt = f"""You are LearnForge, gating a Learner's progress.
The active lesson is currently at stage: {lecture_flow.get('current_stage', 'Unknown')}.
Evaluate if the learner understood the material or answered the quiz correctly. 
If they did, tell them they passed the gate and unlock the next section.
"""
    messages = [SystemMessage(content=system_prompt)] + state.get("messages", [])
    response = await llm.ainvoke(messages)
    
    return {"messages": [response]}
