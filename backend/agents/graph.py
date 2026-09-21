"""LangGraph state machine: master router → persona worker → NBA-scored payload."""

from langgraph.graph import END, START, StateGraph

from backend.agents.master_router import master_router_node, route_by_persona
from backend.agents.state import GraphState
from backend.agents.worker_biz import business_worker_node
from backend.agents.worker_eng import engineering_worker_node
from backend.engine.nba_scorer import build_nba_queue
from backend.models.schemas import DashboardPayload


def _build_dashboard_payload(state: GraphState) -> GraphState:
    chunks = state["retrieved_chunks"]
    state["final_payload"] = DashboardPayload(
        persona=state["persona"],
        welcome_message=_welcome_message(len(chunks)),
        nba_queue=build_nba_queue(chunks),
        context_widgets=chunks,
    )
    return state


def _welcome_message(chunk_count: int) -> str:
    if chunk_count == 0:
        return "Welcome back — nothing new since your last login."
    noun = "update" if chunk_count == 1 else "updates"
    return f"Welcome back — {chunk_count} {noun} since your last login."


def build_graph():
    graph = StateGraph(GraphState)

    graph.add_node("master_router", master_router_node)
    graph.add_node("engineering_worker", engineering_worker_node)
    graph.add_node("business_worker", business_worker_node)
    graph.add_node("build_dashboard", _build_dashboard_payload)

    graph.add_edge(START, "master_router")
    graph.add_conditional_edges(
        "master_router",
        route_by_persona,
        ["engineering_worker", "business_worker"],
    )
    graph.add_edge("engineering_worker", "build_dashboard")
    graph.add_edge("business_worker", "build_dashboard")
    graph.add_edge("build_dashboard", END)

    return graph.compile()


dashboard_graph = build_graph()
