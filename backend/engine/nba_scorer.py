"""Next-Best-Action priority scoring.

Rules-based scorer per the product spec: every retrieved chunk starts at a
base score and picks up modifiers for urgency, recency, and cross-platform
dependencies. An LLM-based scorer can sit behind this same interface later
without changing any caller — `build_nba_queue` is the contract.
"""

import re
from datetime import datetime, timedelta, timezone

from backend.models.schemas import ActionItem, ContextChunk, EventSource

BASE_SCORE = 50
URGENCY_KEYWORD_BONUS = 30
RECENCY_BONUS = 15
RECENCY_WINDOW = timedelta(hours=2)
CROSS_PLATFORM_DEPENDENCY_BONUS = 20
MAX_SCORE = 100

_URGENCY_KEYWORDS = ("p0", "blocker", "blocked", "client escalation", "failing build")
_PR_REFERENCE_PATTERN = re.compile(r"\bPR #\d+|\bpull request #\d+", re.IGNORECASE)

_DEFAULT_ACTION_LABELS: dict[EventSource, str] = {
    EventSource.GITHUB: "View on GitHub",
    EventSource.JIRA: "Open Ticket",
    EventSource.SLACK: "View Message",
    EventSource.GMEET: "Watch Clip",
    EventSource.GCAL: "Open Event",
}


def score_chunk(chunk: ContextChunk, now: datetime | None = None) -> int:
    now = now or datetime.now(timezone.utc)
    score = BASE_SCORE

    searchable_text = f"{chunk.title} {chunk.summary_text} {chunk.metadata}".lower()
    if any(keyword in searchable_text for keyword in _URGENCY_KEYWORDS):
        score += URGENCY_KEYWORD_BONUS

    if now - chunk.timestamp < RECENCY_WINDOW:
        score += RECENCY_BONUS

    # A Workspace chunk (Slack, Meet, Calendar) that name-checks a GitHub PR
    # is the "Marketing is waiting on a PR" case from the spec — amplify it.
    if chunk.source != EventSource.GITHUB and _PR_REFERENCE_PATTERN.search(
        chunk.summary_text
    ):
        score += CROSS_PLATFORM_DEPENDENCY_BONUS

    return min(score, MAX_SCORE)


def build_nba_queue(chunks: list[ContextChunk]) -> list[ActionItem]:
    """Score every chunk and return the resulting queue, highest priority first."""
    items = [
        ActionItem(
            id=chunk.id,
            priority_score=score_chunk(chunk),
            title=chunk.title,
            description=chunk.summary_text,
            action_chip_label=chunk.metadata.get(
                "action_label", _DEFAULT_ACTION_LABELS[chunk.source]
            ),
            action_chip_uri=chunk.pointer_uri,
        )
        for chunk in chunks
    ]
    return sorted(items, key=lambda item: item.priority_score, reverse=True)
