from langgraph.graph import StateGraph, END
from agent.state import AppState
from agent.nodes.context_loader import context_loader_node
from agent.nodes.router import router_node
from agent.nodes.detailed_wf import detailed_wf_node
from agent.nodes.curriculum_wf import curriculum_wf_node
from agent.nodes.lecture_wf import lecture_wf_node
from agent.nodes.gate_wf import gate_wf_node
from agent.nodes.quiz_wf import quiz_wf_node
from agent.nodes.worksheet_wf import worksheet_wf_node
from agent.nodes.research_wf import research_wf_node
from agent.nodes.resource_wf import resource_wf_node
from agent.nodes.diagrams_wf import diagrams_wf_node
from agent.nodes.flashcards_wf import flashcards_wf_node
from agent.nodes.memory_writer import memory_writer_node
from agent.nodes.composer import composer_node

def route_condition(state: AppState):
    return state.get("route", "detailed_wf")

workflow = StateGraph(AppState)

workflow.add_node("context_loader", context_loader_node)
workflow.add_node("router", router_node)
workflow.add_node("detailed_wf", detailed_wf_node)
workflow.add_node("curriculum_wf", curriculum_wf_node)
workflow.add_node("lecture_wf", lecture_wf_node)
workflow.add_node("gate_wf", gate_wf_node)
workflow.add_node("quiz_wf", quiz_wf_node)
workflow.add_node("worksheet_wf", worksheet_wf_node)
workflow.add_node("research_wf", research_wf_node)
workflow.add_node("resource_wf", resource_wf_node)
workflow.add_node("diagrams_wf", diagrams_wf_node)
workflow.add_node("flashcards_wf", flashcards_wf_node)
workflow.add_node("memory_writer", memory_writer_node)
workflow.add_node("composer", composer_node)

workflow.set_entry_point("context_loader")
workflow.add_edge("context_loader", "router")

workflow.add_conditional_edges("router", route_condition, {
    "detailed_wf": "detailed_wf",
    "curriculum_wf": "curriculum_wf",
    "lecture_wf": "lecture_wf",
    "gate_wf": "gate_wf",
    "quiz_wf": "quiz_wf",
    "worksheet_wf": "worksheet_wf",
    "research_wf": "research_wf",
    "resource_wf": "resource_wf",
    "diagrams_wf": "diagrams_wf",
    "flashcards_wf": "flashcards_wf"
})

workflow.add_edge("detailed_wf", "memory_writer")
workflow.add_edge("curriculum_wf", "memory_writer")
workflow.add_edge("lecture_wf", "memory_writer")
workflow.add_edge("gate_wf", "memory_writer")
workflow.add_edge("quiz_wf", "memory_writer")
workflow.add_edge("worksheet_wf", "memory_writer")
workflow.add_edge("research_wf", "memory_writer")
workflow.add_edge("resource_wf", "memory_writer")
workflow.add_edge("diagrams_wf", "memory_writer")
workflow.add_edge("flashcards_wf", "memory_writer")
workflow.add_edge("memory_writer", "composer")
workflow.add_edge("composer", END)

graph = workflow.compile()
