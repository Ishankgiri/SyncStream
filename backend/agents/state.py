"""Shared state shape for the dashboard LangGraph.

Lives in its own module so the router and worker nodes can all depend on it
without importing `graph.py` itself, which would create a circular import
(graph.py is what wires those nodes together).
"""

from datetime import datetime
from typing import TypedDict

from backend.models.schemas import ContextChunk, DashboardPayload, PersonaType


class GraphState(TypedDict):
    user_id: str
    persona: PersonaType
    query_time_range: datetime | None
    retrieved_chunks: list[ContextChunk]
    final_payload: DashboardPayload | None
