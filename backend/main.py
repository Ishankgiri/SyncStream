"""FastAPI application entry point."""

from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.agents.graph import dashboard_graph
from backend.models.schemas import DashboardPayload, PersonaType

app = FastAPI(title="SyncStream API")

# Local Next.js dev server. Update this once the frontend has a deployed origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/dashboard", response_model=DashboardPayload)
def get_dashboard(
    user_id: str, persona: PersonaType, since: datetime | None = None
) -> DashboardPayload:
    """Run the persona-routed agent graph and return the rendered briefing.

    `since` scopes the query to chunks created after that time (conceptually,
    the user's last login). Omit it to return everything currently indexed.
    """
    result = dashboard_graph.invoke(
        {
            "user_id": user_id,
            "persona": persona,
            "query_time_range": since,
            "retrieved_chunks": [],
            "final_payload": None,
        }
    )
    return result["final_payload"]
