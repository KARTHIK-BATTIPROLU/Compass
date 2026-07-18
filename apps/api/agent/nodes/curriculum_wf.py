from agent.state import AppState
from agent.llm import get_llm
from langchain_core.messages import SystemMessage
from langfuse import observe

@observe()
async def curriculum_wf_node(state: AppState):
    llm = get_llm(temperature=0.1)
    
    user = state.get("user", {})
    role = user.get("role", "learner")
    class_level = state.get("class_level", "")
    curriculum_ctx = state.get("curriculum_ctx", [])
    
    ctx_str = "\n\n".join([f"Topic: {c['metadata'].get('topic', 'N/A')}\n{c['content']}" for c in curriculum_ctx])
    
    system_prompt = f"""You are LearnForge, an AI learning assistant.
The user is a {role}. Context: {class_level}.
STRICT SYLLABUS CONSTRAINT:
You MUST base your explanation primarily on the provided curriculum context below.
If the curriculum context does not cover the user's question, gently redirect them to the syllabus topics.

CURRICULUM CONTEXT:
{ctx_str if ctx_str else "No specific curriculum chunks found for this query."}
"""

    messages = [SystemMessage(content=system_prompt)] + state.get("messages", [])
    
    response = await llm.ainvoke(messages)
    
    return {"messages": [response]}
