"""Business/Workspace Worker: retrieves GMeet/GCal/Slack chunks for the PM persona."""

from backend.agents.state import GraphState
from backend.data_pipeline.vector_store import query_chunks_by_persona
from backend.models.schemas import PersonaType


def business_worker_node(state: GraphState) -> GraphState:
    state["retrieved_chunks"] = query_chunks_by_persona(
        PersonaType.PRODUCT_MANAGER, state["query_time_range"]
    )
    return state
