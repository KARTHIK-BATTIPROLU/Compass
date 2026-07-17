from typing import Literal

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.agent.nodes.content_generator import content_generator
from app.agent.nodes.human_review_gate import human_review_gate
from app.agent.nodes.intent_router import intent_router
from app.agent.nodes.scraper_node import scrape_reference
from app.agent.nodes.weak_spot_tracker import weak_spot_tracker
from app.agent.state import AgentState

_checkpointer = MemorySaver()
_compiled = None


async def _passthrough(state: AgentState) -> dict:
    return {}


def _needs_scrape(state: AgentState) -> Literal["scraper_node", "skip_scrape"]:
    if "scrape_reference" in (state.get("detected_intents") or []):
        return "scraper_node"
    return "skip_scrape"


def _after_review(state: AgentState) -> Literal["content_generator", "__end__"]:
    if state.get("review_status") == "regenerate":
        return "content_generator"
    return END


def build_graph():
    global _compiled
    if _compiled is not None:
        return _compiled

    graph = StateGraph(AgentState)
    graph.add_node("intent_router", intent_router)
    graph.add_node("weak_spot_tracker", weak_spot_tracker)
    graph.add_node("scraper_node", scrape_reference)
    graph.add_node("skip_scrape", _passthrough)
    graph.add_node("content_generator", content_generator)
    graph.add_node("human_review_gate", human_review_gate)

    graph.add_edge(START, "intent_router")
    graph.add_edge("intent_router", "weak_spot_tracker")
    graph.add_conditional_edges("weak_spot_tracker", _needs_scrape)
    graph.add_edge("scraper_node", "content_generator")
    graph.add_edge("skip_scrape", "content_generator")
    graph.add_edge("content_generator", "human_review_gate")
    graph.add_conditional_edges("human_review_gate", _after_review)

    _compiled = graph.compile(checkpointer=_checkpointer)
    return _compiled


def get_graph():
    return build_graph()
