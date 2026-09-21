"""Master Agent: entry point and persona router for the dashboard graph.

Per the architecture, persona is decided once, up front, and everything
downstream is strictly scoped to it — Engineering data must not reach a PM
dashboard and vice versa. This module is the single place that decision
gets made.
"""

from typing import Literal

from backend.agents.state import GraphState
from backend.models.schemas import PersonaType


def master_router_node(state: GraphState) -> GraphState:
    return state


def route_by_persona(state: GraphState) -> Literal["engineering_worker", "business_worker"]:
    if state["persona"] == PersonaType.DEVELOPER:
        return "engineering_worker"
    return "business_worker"
