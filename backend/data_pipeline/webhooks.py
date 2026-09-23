"""Simulated webhook ingestion route.

Stands in for the real GitHub/Jira/Slack/GMeet webhook receivers. A real
receiver's only extra job is mapping each provider's payload shape into this
same `SimulatedEvent` shape — `pointer_uri` and `metadata` pulled from known
payload fields, `raw_text` assembled from whatever prose the provider gives
(a PR description, a ticket body, a transcript excerpt) — then handing off
to the same summarize-and-store path used here.
"""

from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel

from backend.data_pipeline.summarizer import summarize_event
from backend.data_pipeline.vector_store import add_chunk
from backend.models.schemas import ContextChunk, EventSource

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


class SimulatedEvent(BaseModel):
    source: EventSource
    raw_text: str
    pointer_uri: str
    metadata: dict = {}
    timestamp: datetime | None = None


@router.post("/simulate", response_model=ContextChunk)
def simulate_webhook(event: SimulatedEvent) -> ContextChunk:
    chunk = summarize_event(
        source=event.source,
        raw_text=event.raw_text,
        pointer_uri=event.pointer_uri,
        metadata=event.metadata,
        timestamp=event.timestamp,
    )
    add_chunk(chunk)
    return chunk
