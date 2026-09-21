"""Pydantic models — single source of truth for the SyncStream data contracts.

These schemas are shared, conceptually, across three layers of the system:
ingestion (data_pipeline writes ContextChunks), orchestration (agents read
chunks and produce ActionItems), and the API boundary (DashboardPayload is
what the frontend renders). Changing a field here changes all three, so
this file should stay the single place these shapes are defined.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class PersonaType(str, Enum):
    DEVELOPER = "developer"
    PRODUCT_MANAGER = "product_manager"


class EventSource(str, Enum):
    GITHUB = "github"
    JIRA = "jira"
    SLACK = "slack"
    GMEET = "gmeet"
    GCAL = "gcal"


class ContextChunk(BaseModel):
    """A single summarized event, as written to the vector store at ingestion time.

    This is the only unit of data agents read at runtime — raw source data
    (full PR diffs, full meeting transcripts) is never fetched during a
    dashboard request. `pointer_uri` is what lets the frontend deep-link back
    to that raw data if the user chooses to drill in.
    """

    id: str
    source: EventSource
    target_persona: PersonaType
    title: str
    summary_text: str
    pointer_uri: str
    timestamp: datetime
    metadata: dict


class ActionItem(BaseModel):
    """A single entry in a persona's Next-Best-Action queue, ranked by priority_score."""

    id: str
    priority_score: int
    title: str
    description: str
    action_chip_label: str
    action_chip_uri: str


class DashboardPayload(BaseModel):
    """The full response the frontend renders as the 'Welcome Back Briefing'."""

    persona: PersonaType
    welcome_message: str
    nba_queue: list[ActionItem]
    context_widgets: list[ContextChunk]
