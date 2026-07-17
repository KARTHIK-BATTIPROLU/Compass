from agent.state import AppState
from langchain_groq import ChatGroq
import os
from langfuse.decorators import observe

@observe()
async def router_node(state: AppState) -> AppState:
    modes = state.get("modes", [])
    modes_lower = [m.lower() for m in modes]
    
    user = state.get("user", {})
    lecture_flow = state.get("lecture_flow", {})
    
    # Gating check
    if user.get("role") == "learner" and lecture_flow.get("active_lesson"):
        return {"route": "gate_wf"}
    
    if "quiz" in modes_lower or "quiz me" in modes_lower:
        return {"route": "quiz_wf"}
        
    if "worksheet" in modes_lower:
        return {"route": "worksheet_wf"}
    
    if "update & research" in modes_lower or "research" in modes_lower:
        return {"route": "research_wf"}
        
    if "resource" in modes_lower:
        return {"route": "resource_wf"}
    
    if "diagrams" in modes_lower:
        return {"route": "diagrams_wf"}
        
    if "flashcards" in modes_lower:
        return {"route": "flashcards_wf"}
    
    if "curriculum" in modes_lower:
        return {"route": "curriculum_wf"}
        
    if "lecture script" in modes_lower:
        return {"route": "lecture_wf"}
    
    if "detailed" in modes_lower:
        return {"route": "detailed_wf"}
        
    return {"route": "detailed_wf"}
