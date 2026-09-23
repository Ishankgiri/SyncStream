"""Turns raw webhook event text into a ContextChunk via Gemini.

The model is only ever asked for the three things that genuinely require
judgment: a title, a <3-sentence summary, and which persona the event
matters most to. `pointer_uri`, `timestamp`, and structured `metadata` are
supplied by the caller (extracted deterministically from the source
payload upstream) rather than asked of the model — an LLM has no reliable
way to know the real deep link back to a PR or ticket, and asking it to
produce one risks a hallucinated URI ending up in front of a user.
"""

import os
import uuid
from datetime import datetime, timezone

from google import genai
from pydantic import BaseModel

from backend.models.schemas import ContextChunk, EventSource, PersonaType

_MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash-001")

_PROMPT_TEMPLATE = """You are the ingestion summarizer for SyncStream, a tool that briefs \
engineers and product managers on what happened since they last logged in.

Summarize the following {source} event in under 3 sentences. Preserve any urgency \
markers (e.g. "P0", "blocked", "client escalation") and any referenced PR or ticket \
numbers (e.g. "PR #402") exactly as they appear in the source text — other parts of \
this system scan the summary for those exact terms to flag priority.

Classify which persona this event matters most to:
- "developer": code changes, infrastructure, technical blockers, CI/CD, schema changes
- "product_manager": timelines, client communication, cross-team dependencies, \
launch/release decisions

Event:
{raw_text}
"""


class _GeminiDraft(BaseModel):
    title: str
    summary_text: str
    target_persona: PersonaType


_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(
            vertexai=True,
            project=os.environ["GOOGLE_CLOUD_PROJECT"],
            location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"),
        )
    return _client


def _draft_from_text(source: EventSource, raw_text: str) -> _GeminiDraft:
    response = _get_client().models.generate_content(
        model=_MODEL_NAME,
        contents=_PROMPT_TEMPLATE.format(source=source.value, raw_text=raw_text),
        config={
            "response_mime_type": "application/json",
            "response_schema": _GeminiDraft,
        },
    )
    return _GeminiDraft.model_validate_json(response.text)


def summarize_event(
    source: EventSource,
    raw_text: str,
    pointer_uri: str,
    metadata: dict,
    timestamp: datetime | None = None,
) -> ContextChunk:
    draft = _draft_from_text(source, raw_text)
    return ContextChunk(
        id=str(uuid.uuid4()),
        source=source,
        target_persona=draft.target_persona,
        title=draft.title,
        summary_text=draft.summary_text,
        pointer_uri=pointer_uri,
        timestamp=timestamp or datetime.now(timezone.utc),
        metadata=metadata,
    )
