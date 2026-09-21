# SyncStream

An autonomous, cross-platform knowledge & decision copilot that eliminates enterprise context collapse. SyncStream ingests events from engineering and business tools (GitHub, Jira, Slack, Google Workspace), summarizes them into semantically-indexed chunks in real time, and — on login — renders a persona-specific "Welcome Back Briefing" with an algorithmic Next-Best-Action (NBA) queue telling the user exactly what to do next.

Built for the Google AI Builder Cup.

## Core Idea

Traditional enterprise search returns generic results and leaves the user to figure out priority. SyncStream instead:

1. **Ingests continuously, not at query time.** Webhooks (`PR_MERGED`, `MEETING_ENDED`, etc.) trigger a lightweight Gemini summarization step that writes a short chunk + a deep-link pointer into a vector store — never raw data.
2. **Routes by persona.** A LangGraph Master Agent identifies whether the user is a Developer or a Product Manager and dispatches to a domain-specific Worker Agent (Engineering vs. Business/Workspace). Persona data does not bleed across unless a cross-platform dependency explicitly links it.
3. **Prescribes, not just summarizes.** An NBA scoring engine ranks every retrieved chunk 0–100 (deadline pressure, urgency keywords, cross-platform dependencies, persona relevance) and returns an actionable queue, not a wall of text.

This gives sub-3-second dashboard loads because runtime never does live API scraping — it only reads pre-chunked summaries.

## Architecture at a Glance

```
Webhook event → Gemini summarizer → ContextChunk (Vertex AI Vector Search)
                                            │
User login → LangGraph Master Agent (persona router)
                                            │
                    ┌───────────────────────┴───────────────────────┐
              Engineering Worker                          Business/Workspace Worker
              (GitHub / Jira)                              (GMeet / GCal / Slack)
                    └───────────────────────┬───────────────────────┘
                                    NBA Scorer (0–100)
                                            │
                              DashboardPayload (JSON) → Next.js UI
```

See `SYNCSTREAM_ARCHITECTURE.md` (or the original build doc supplied to the project) for the full PRD: data models, scoring rules, and phase-by-phase build plan. This README tracks the *current, actual* state of the codebase — the build doc is the north star, this file is where we are relative to it.

## Tech Stack

- **Backend / AI Orchestration:** Python 3.11+, FastAPI, LangGraph, Vertex AI SDK (Gemini 1.5 Pro/Flash), Vertex AI Vector Search
- **Frontend:** React 18, Next.js 14 (App Router), TypeScript, Tailwind CSS
- **Deployment (target):** Cloud Run (backend), Firebase Hosting (frontend)
- **MVP integration scope:** Live — GitHub (webhooks + API), simulated Google Meet transcripts. Mocked — Jira, Slack (static JSON payloads).

## Monorepo Layout (target)

```
syncstream/
├── frontend/           # Next.js 14 App Router, Tailwind, TS
│   └── src/{app,components/{widgets,nba},types}
├── backend/
│   ├── main.py                  # FastAPI app
│   ├── agents/                  # LangGraph state machine + nodes
│   ├── engine/nba_scorer.py     # Priority scoring
│   ├── data_pipeline/           # Webhooks, Gemini summarizer, vector store I/O
│   ├── models/schemas.py        # Pydantic models — single source of truth
│   └── mocks/                   # Simulated Jira/Slack payloads
└── AGENT_CHANGELOG.md   # AI agent session handoff log
```

## Project Status

**Phase: 2 complete.** The backend runs end-to-end: `GET /api/dashboard?user_id=...&persona=...` invokes a LangGraph (Master router → persona-scoped Worker agent → NBA-scored payload assembly) and returns a real `DashboardPayload`. The chunk store is in-memory and empty until Phase 3's ingestion pipeline exists, so today the API is provably correct but has nothing to show — that's the next phase.

Planned phases (see build doc for detail):

- [x] **Phase 1** — Monorepo scaffolding, `requirements.txt` / `package.json`, `schemas.py`
- [x] **Phase 2** — FastAPI server + LangGraph orchestration (Master + Worker agents, NBA scorer)
- [ ] **Phase 3** — Simulated data pipeline (webhook ingestion + Gemini chunking)
- [ ] **Phase 4** — Next.js frontend widgets (Velocity Timeline, PR Diff Card, NBA Queue, Action Chips)

See `AGENT_CHANGELOG.md` for the detailed, file-by-file state and `PERSONA.md` for the coding standard this codebase follows.

## Working With This Repo (for AI agents and humans)

This project uses **`AGENT_CHANGELOG.md`** as the persistent handoff document between work sessions. Read it before making changes — it holds the current state, active work, and known issues in more granular detail than this README. Update it before every commit.

This README should be kept in sync as the project's scope, architecture, and trajectory evolve — treat it as living documentation, not a one-time snapshot.

## Getting Started

Not yet runnable — see Project Status above. Setup instructions will be added here once Phase 1 scaffolding lands.
