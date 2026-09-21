"""Engineering Worker: retrieves GitHub/Jira chunks for the Developer persona."""

from backend.agents.state import GraphState
from backend.data_pipeline.vector_store import query_chunks_by_persona
from backend.models.schemas import PersonaType


def engineering_worker_node(state: GraphState) -> GraphState:
    state["retrieved_chunks"] = query_chunks_by_persona(
        PersonaType.DEVELOPER, state["query_time_range"]
    )
    return state
