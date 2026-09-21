"""Read/write interface to the chunk store.

This is an in-memory stand-in for Vertex AI Vector Search. Phase 3 wires the
webhook ingestion pipeline to `add_chunk`, and will eventually swap the
storage backend here for real Vertex AI Vector Search calls. Everything else
in the system — the LangGraph workers, the API — depends only on this
module's two functions, not on how chunks are actually stored, so that swap
should not require touching them.
"""

from datetime import datetime

from backend.models.schemas import ContextChunk, PersonaType

_chunks: list[ContextChunk] = []


def add_chunk(chunk: ContextChunk) -> None:
    _chunks.append(chunk)


def query_chunks_by_persona(
    persona: PersonaType, since: datetime | None = None
) -> list[ContextChunk]:
    """Return chunks for a persona, newest first, optionally since a given time.

    This is the only read path agents use at runtime — per the architecture's
    "no live scraping" constraint, nothing here reaches out to GitHub, Jira,
    or any other source directly.
    """
    matches = [chunk for chunk in _chunks if chunk.target_persona == persona]
    if since is not None:
        matches = [chunk for chunk in matches if chunk.timestamp >= since]
    return sorted(matches, key=lambda chunk: chunk.timestamp, reverse=True)
