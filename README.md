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

- **Backend / AI Orchestration:** Python 3.11+, FastAPI, LangGraph, Gemini via Vertex AI (`google-genai`), Vertex AI Vector Search (target; currently an in-memory store, see Project Status)
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
│   ├── data_pipeline/           # Webhook route, Gemini summarizer, vector store I/O
│   ├── models/schemas.py        # Pydantic models — single source of truth
│   └── mocks/                   # Sample webhook payloads (GitHub, Jira, Slack, GMeet)
├── PERSONA.md            # Coding standard — read before writing code
└── AGENT_CHANGELOG.md    # AI agent session handoff log
```

## Project Status

**Phase: 3 complete.** The backend is fully wired end-to-end: `POST /webhooks/simulate` takes a raw event, summarizes it with Gemini, and stores it as a `ContextChunk`; `GET /api/dashboard` runs the LangGraph against those stored chunks and returns a real, NBA-scored `DashboardPayload`. Sample payloads for all four MVP sources live in `backend/mocks/`. No UI yet — that's Phase 4. The chunk store is still in-memory (not real Vertex AI Vector Search), which is fine for this stage but won't survive a server restart or run across multiple instances.

Planned phases (see build doc for detail):

- [x] **Phase 1** — Monorepo scaffolding, `requirements.txt` / `package.json`, `schemas.py`
- [x] **Phase 2** — FastAPI server + LangGraph orchestration (Master + Worker agents, NBA scorer)
- [x] **Phase 3** — Simulated data pipeline (webhook ingestion + Gemini chunking)
- [ ] **Phase 4** — Next.js frontend widgets (Velocity Timeline, PR Diff Card, NBA Queue, Action Chips)

See `AGENT_CHANGELOG.md` for the detailed, file-by-file state and `PERSONA.md` for the coding standard this codebase follows.

## Working With This Repo (for AI agents and humans)

This project uses **`AGENT_CHANGELOG.md`** as the persistent handoff document between work sessions. Read it before making changes — it holds the current state, active work, and known issues in more granular detail than this README. Update it before every commit.

This README should be kept in sync as the project's scope, architecture, and trajectory evolve — treat it as living documentation, not a one-time snapshot.

## Getting Started

Backend setup uses [uv](https://docs.astral.sh/uv/) rather than raw `pip`/`venv`. Everything below runs from the repo root.

### 1. Create the environment and install dependencies

```bash
uv venv .venv --python 3.12   # backend needs Python 3.11+; adjust the version if you have a different 3.11+ installed
source .venv/bin/activate     # Windows: .venv\Scripts\activate
uv pip install -r backend/requirements.txt
```

`uv pip install` reads the same `requirements.txt` `pip` would — nothing about the file itself changes, only the installer. If you'd rather skip activating the venv, prefix any command below with `uv run --python .venv/bin/python` instead.

To add or upgrade a dependency later: edit `backend/requirements.txt`, then re-run `uv pip install -r backend/requirements.txt` (or `uv pip install -U <package>` for a one-off bump, then reflect the new pin in the file by hand).

### 2. Configure Gemini access

The webhook summarizer (`backend/data_pipeline/summarizer.py`) calls Gemini through Vertex AI, which needs a GCP project with the Vertex AI API enabled and local application-default credentials:

```bash
gcloud auth application-default login
cp backend/.env.example backend/.env
# edit backend/.env — set GOOGLE_CLOUD_PROJECT to your project id
```

`GET /api/dashboard` never touches Gemini or any external API — only `POST /webhooks/simulate` does, matching the "no live calls at dashboard-read time" constraint.

### 3. Run the server

```bash
uvicorn backend.main:app --reload
```

Serves on `http://localhost:8000`. Interactive API docs at `http://localhost:8000/docs`.

### 4. Exercise the full flow

With the server running, in another terminal:

```bash
# Empty dashboard — nothing ingested yet
curl "http://localhost:8000/api/dashboard?user_id=u1&persona=developer"

# Ingest the sample events (requires Gemini access, step 2 above)
curl -X POST http://localhost:8000/webhooks/simulate \
  -H "Content-Type: application/json" \
  -d @backend/mocks/github_pr_merged.json

curl -X POST http://localhost:8000/webhooks/simulate \
  -H "Content-Type: application/json" \
  -d @backend/mocks/jira_blocker.json

curl -X POST http://localhost:8000/webhooks/simulate \
  -H "Content-Type: application/json" \
  -d @backend/mocks/slack_client_escalation.json

curl -X POST http://localhost:8000/webhooks/simulate \
  -H "Content-Type: application/json" \
  -d @backend/mocks/gmeet_standup.json

# Now the dashboards have content, scored and sorted by priority
curl "http://localhost:8000/api/dashboard?user_id=u1&persona=developer" | python3 -m json.tool
curl "http://localhost:8000/api/dashboard?user_id=u1&persona=product_manager" | python3 -m json.tool
```

You should see the developer dashboard pick up only the GitHub/Jira chunks and the PM dashboard only the Slack/GMeet chunks (persona isolation), with the P0/blocked items scored highest.

The chunk store is in-memory and per-process — restarting the server clears it, so you'll need to re-run the `curl -X POST .../webhooks/simulate` calls after each restart.
