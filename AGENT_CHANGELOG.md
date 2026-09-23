# SyncStream — Agent Changelog

This is the persistent handoff document between AI work sessions on this project. Read the **Current State** section before making any changes. Update this file before every commit — it should let an agent with zero conversation history pick up safely.

**Before writing or editing any code, read [`PERSONA.md`](PERSONA.md)** — the project's coding standard (comment philosophy, how much abstraction is appropriate, what "clean" means here). This changelog tracks *what* was built and *why*; `PERSONA.md` governs *how* it should be written. Apply it every session, not just the one it was written in.

Keep this file compact: a maintained "Current State" snapshot at the top, plus append-only session history below. Do not let it become a full transcript.

---

## Current State

**Project:** SyncStream — dual-persona, multi-agent project intelligence copilot (Developer vs. Product Manager briefings) built on a federated-retrieval / chunked-caching architecture. Full product/architecture spec lives in the original build doc (Google AI Builder Cup submission); `README.md` carries a condensed version.

**Phase:** Phase 3 complete. Backend is fully wired end-to-end: `POST /webhooks/simulate` → Gemini summarizer → `ContextChunk` in the vector store; `GET /api/dashboard` → LangGraph → NBA-scored `DashboardPayload`. Verified with the real Gemini call stubbed (no GCP credentials in the build environment) but every other layer — routing, persona isolation, scoring, FastAPI wiring — exercised for real via a live server process. No frontend yet — that's Phase 4.

**Repo contents right now:**
- `backend/models/schemas.py` — `PersonaType`, `EventSource`, `ContextChunk`, `ActionItem`, `DashboardPayload` (pydantic v2, unchanged since Phase 1).
- `backend/requirements.txt` — fastapi 0.141.1, uvicorn 0.53.0, pydantic 2.13.5, langgraph 1.2.12, langchain-core 1.6.4, python-dotenv 1.2.3, **google-genai 2.25.0** (replaces the unused `google-cloud-aiplatform` placeholder from Phase 1/2 — this is the package actually used to call Gemini).
- `backend/data_pipeline/vector_store.py` — in-memory chunk store: `add_chunk`, `query_chunks_by_persona(persona, since=None)`. Stands in for Vertex AI Vector Search; the backing store can later be swapped for real Vertex calls without touching callers.
- `backend/data_pipeline/summarizer.py` — `summarize_event(source, raw_text, pointer_uri, metadata, timestamp=None) -> ContextChunk`. Calls Gemini (via `google.genai.Client(vertexai=True, ...)`) for only title/summary/persona classification — `pointer_uri`, `metadata`, and `timestamp` are supplied by the caller, never asked of the model (avoids a hallucinated deep link). Requires `GOOGLE_CLOUD_PROJECT` env var; `GOOGLE_CLOUD_LOCATION` and `GEMINI_MODEL` are optional with defaults.
- `backend/data_pipeline/webhooks.py` — `POST /webhooks/simulate` (`SimulatedEvent`: source, raw_text, pointer_uri, metadata, timestamp) → `summarize_event` → `vector_store.add_chunk`.
- `backend/mocks/*.json` — one sample payload per MVP source (`github_pr_merged`, `jira_blocker`, `slack_client_escalation`, `gmeet_standup`), shaped to POST directly to `/webhooks/simulate`.
- `backend/.env.example` — `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`, `GEMINI_MODEL`. `main.py` loads `backend/.env` explicitly by path (not a bare `load_dotenv()`) so it's found regardless of the process's working directory.
- `backend/agents/state.py`, `master_router.py`, `worker_eng.py`, `worker_biz.py`, `graph.py`, `backend/engine/nba_scorer.py` — unchanged since Phase 2.
- `backend/main.py` — FastAPI app, CORS open to `localhost:3000`, `GET /health`, `GET /api/dashboard?user_id&persona&since`, `POST /webhooks/simulate` (via included router).
- `PERSONA.md` — coding standard. Read before writing code.
- `frontend/package.json` — unchanged since Phase 1 (no app code yet).
- `.gitignore`, `README.md`, `AGENT_CHANGELOG.md`.

**Active work:** None in progress. Waiting on the user to confirm kickoff for **Phase 4** (Next.js frontend widgets).

**Known issues / traps:**
- The vector store is in-memory and process-local — it resets on every server restart. Re-POST the mock payloads after each restart if you want a populated dashboard.
- `summarize_event` will raise a `KeyError` on `GOOGLE_CLOUD_PROJECT` if that env var isn't set — deliberate, no fallback: an ingestion call with no Gemini access should fail loudly, not silently degrade.
- Build doc explicitly forbids live API scraping at runtime; only `POST /webhooks/simulate` calls out to Gemini — `GET /api/dashboard` never calls any external API, only reads the store.
- Build doc explicitly forbids persona data bleed — enforced by construction since each worker only ever queries its own persona's chunks. The NBA scorer's cross-platform bonus is the one deliberate exception, and it only ever inspects a chunk's own text, never the other persona's chunk set.
- MVP scope: GitHub is the only *live* integration in the real product vision; Jira and Slack stay mocked via static JSON; Google Meet transcripts are simulated. Phase 3 built the ingestion *mechanism* (the webhook route + summarizer) generically for all sources — hooking up a real GitHub webhook receiver (mapping GitHub's actual payload shape into `SimulatedEvent`) is not yet done and isn't required by the build doc's MVP scope.
- Gemini calls are **unverified against the live API** in this environment (no GCP credentials available). Verified instead by stubbing `summarizer._draft_from_text` and confirming everything downstream (assembly, storage, retrieval, scoring, HTTP wiring) behaves correctly. The user should smoke-test the real Gemini call themselves once `backend/.env` is configured (see README's Getting Started).
- Discovered and removed an abandoned `uv init` scaffold (`backend/pyproject.toml`, `backend/uv.lock`, `backend/.python-version`, empty `backend/README.md`, `backend/src/`, a stray `backend/.venv`, and root `src/syncstream/__init__.py`) that the user had generated in their own terminal while experimenting with uv, separately from this session. User confirmed (2026-09-23): keep the `requirements.txt` + `uv pip install` flow rather than migrating to a native uv project — don't reintroduce that scaffold without asking again.
- `httpx` was used transiently (in a throwaway venv, not committed) to smoke-test `TestClient`; it is not in `requirements.txt` and isn't needed until an actual test suite is set up.

**Next steps:** Ask the user to confirm before starting Phase 4 (per the build doc's own execution protocol, phases should be done one at a time, not all at once).

**Code style standard:** see [`PERSONA.md`](PERSONA.md) — read it before writing code, every session.

---

## Session History

### Session 1 — 2026-09-22

**What was done:**
- Received and reviewed the full SyncStream architecture/build doc (product PRD + AI agent build instructions) from the user.
- Created `README.md`: project overview, architecture diagram, tech stack, monorepo layout, and phase checklist, to be kept in sync as scope evolves.
- Created this file (`AGENT_CHANGELOG.md`) per the user's requested agent-handoff protocol.
- User confirmed kickoff for Phase 1 and gave a standing code-style directive (see "Code style standard" above) — comments as a last resort, no over-engineering, proportionate implementations.
- Executed **Phase 1**: created the `backend/{agents,engine,data_pipeline,models,mocks}` and `frontend/src/{app,components/{widgets,nba},types}` directory trees; wrote `backend/requirements.txt`, `frontend/package.json`, and `backend/models/schemas.py` (the five Pydantic models from the build doc, verbatim field-for-field); added `__init__.py` to each backend package; extended `.gitignore` with a Node/Next.js section.
- Updated `README.md` and this changelog to reflect Phase 1 completion.

**Decisions:**
- Treated `README.md` as the living, human-facing project narrative and `AGENT_CHANGELOG.md` as the machine/agent-facing state + session log, per the user's explicit request to maintain both, with distinct purposes (README = vision/status, changelog = handoff detail).
- Kept `frontend/` to just `package.json` in Phase 1 (no `tsconfig.json`/Tailwind config/app files yet) — those belong with the actual components in Phase 4, per the build doc's phase boundaries; adding them now would be inert config with nothing to configure.
- Added `__init__.py` files to backend packages since they're structurally required for the modules to be importable, not scope creep.

**Verification:** No automated tests yet (no logic exists to test). Verified by inspection: directory tree matches the build doc's monorepo layout exactly; `schemas.py` field names/types match the doc's schema listing.

**Unfinished / next steps:** Phases 2–4 remain (FastAPI server + LangGraph orchestration; simulated webhook/Gemini summarization pipeline; Next.js frontend widgets). Next agent/session should confirm with the user before starting Phase 2, then implement the Master Agent router and Engineering/Business Worker nodes per section 5.A of the build doc.

**Commit:** _(record hash here once committed)_

### Session 2 — 2026-09-22

**What was done:**
- User asked to record the coding-practices directive from the previous message as a standing reference file, checked before any code is written — created `PERSONA.md` (comment philosophy with the before/after example the user supplied, proportionate-implementation rules) and pointed to it from the top of this changelog and from the "Code style standard" line.
- Executed **Phase 2**: FastAPI server + LangGraph Master/Worker orchestration. New files: `backend/data_pipeline/vector_store.py`, `backend/agents/{state,master_router,worker_eng,worker_biz,graph}.py`, `backend/engine/nba_scorer.py`, `backend/main.py`. See Current State above for what each does.
- Discovered Phase 1's `requirements.txt` pins were stale (guessed, not verified) — installed into a real venv (Python 3.12, via `/opt/homebrew/bin/python3.12`; the system `python3` is 3.9.6 and too old for this project) and repinned to versions confirmed to actually install and work: fastapi 0.141.1, uvicorn 0.53.0, pydantic 2.13.5, langgraph 1.2.12, langchain-core 1.6.4, python-dotenv 1.2.3.
- Verified the graph and API for real: ran `dashboard_graph.invoke(...)` against an empty store (returns empty queue, no errors), then seeded three `ContextChunk`s (two developer, one PM — one of them referencing `PR #402` and using the word "blocked") and confirmed (a) persona isolation — each persona only ever saw its own chunks, (b) NBA scoring math — a P0/"blocked" chunk under 2h old scored 95–100 as expected from the modifier rules, an old unflagged chunk stayed at the base 50, (c) the FastAPI endpoint via `TestClient` returns 200 with a valid payload and 422 on an invalid persona value.
- Deleted the throwaway verification venv after testing; nothing from it is committed.

**Decisions:**
- Put `GraphState` in its own `backend/agents/state.py` rather than in `graph.py`, so the router/worker node modules can import the state type without a circular import against the module that wires them together.
- Kept `master_router_node` as a real (if currently trivial) pass-through node rather than folding routing entirely into the conditional-edge function — the build doc calls for an explicit "Master Agent router node," and it's a natural place to hang future cross-cutting concerns (e.g. defaulting `query_time_range`, logging) without touching persona-routing logic.
- NBA scorer's urgency-keyword check searches `title + summary_text + metadata` rather than metadata alone as the doc's shorthand literally says — chunk text is where these signals actually show up in realistic data; metadata-only matching would silently miss the doc's own worked examples (e.g. "Fix P0 auth schema bug" as a title, not a metadata field).
- Cross-platform dependency bonus implemented as a simple `PR #<n>` regex match on a non-GitHub chunk's text, rather than actually cross-referencing the chunk against the Engineering persona's chunk set — the doc's own description ("explicitly mentions ... e.g., GitHub PR ID") is satisfied by the mention itself, and real cross-referencing would need the ingestion/linking system Phase 3 hasn't built yet. Revisit if Phase 3 introduces structured chunk-to-chunk links.
- Did not seed the vector store with permanent demo data — an empty store on a fresh process is the correct, honest state until Phase 3's ingestion pipeline exists; seeding now would blur the Phase 2/3 boundary and risk looking like real ingestion when it isn't.
- Did not add `httpx` to `requirements.txt` — it was only needed for `TestClient` during manual verification, not for the app to run.

**Verification:** Ran directly (not just read) in a real Python 3.12 venv: (1) graph invocation against empty store, (2) graph invocation with seeded multi-persona chunks confirming isolation and all three NBA modifiers (urgency, recency, cross-platform) independently, (3) FastAPI `TestClient` hitting `/health` and `/api/dashboard`, including one invalid-input case. All passed as expected; no automated test suite exists yet (not requested).

**Unfinished / next steps:** Phase 3 (simulated webhook ingestion: `POST /webhooks/simulate` → Gemini summarizer → `vector_store.add_chunk`) and Phase 4 (Next.js frontend) remain. Next session should confirm Phase 3 scope with the user, then read `PERSONA.md` before writing the summarizer prompt/parsing code.

**Commit:** _(record hash here once committed)_

### Session 3 — 2026-09-23

**What was done:**
- Executed **Phase 3**: `backend/data_pipeline/summarizer.py` (Gemini call via `google-genai`, `vertexai=True`) and `backend/data_pipeline/webhooks.py` (`POST /webhooks/simulate`), wired into `main.py`. Added `backend/mocks/{github_pr_merged,jira_blocker,slack_client_escalation,gmeet_standup}.json` as ready-to-POST sample events, and `backend/.env.example` for the required `GOOGLE_CLOUD_PROJECT`/`GOOGLE_CLOUD_LOCATION`/`GEMINI_MODEL` vars.
- Repinned `requirements.txt`: swapped the unused `google-cloud-aiplatform` placeholder for `google-genai==2.25.0`, the package actually used.
- Verified `google.genai.Client`'s constructor and `models.generate_content(..., config={"response_schema": ...})` signatures directly against the installed package (structured-output support confirmed) before writing code against them.
- Updated `README.md`'s Getting Started section with real, tested `uv` setup/run/test instructions (the user is migrating off `pip`) — `uv venv`, `uv pip install -r backend/requirements.txt`, `uvicorn backend.main:app --reload`, then a full `curl` walkthrough posting all four mock events and reading both persona dashboards back.
- **Ran the exact documented commands for real**, not just read them: created the `uv venv` at repo root, `uv pip install`'d `requirements.txt` through it, started the real server with `uvicorn`, and hit it with real HTTP requests (`curl` and a Python client) — including posting all four mock payloads through `/webhooks/simulate` and confirming both dashboards. Gemini's actual network call was stubbed (`summarizer._draft_from_text` patched) since this environment has no GCP credentials; every other layer (FastAPI routing, summarizer assembly, vector store, LangGraph, NBA scoring) ran unstubbed and for real.
- Mid-session, discovered untracked files inside the repo I hadn't created (`backend/pyproject.toml`, `backend/uv.lock`, `backend/.python-version`, an empty `backend/README.md`, `backend/src/backend/__init__.py`, root `src/syncstream/__init__.py`, and a second `backend/.venv`) — file timestamps and the embedded author (`Ishankgiri <ishankkaku@gmail.com>`, matching local `git config`) indicated the user had run `uv init` themselves, outside this conversation, while exploring uv. Per the "investigate before deleting" rule, stopped and asked the user how to proceed rather than assuming.
- User chose (2026-09-23): keep the `requirements.txt` + `uv pip install` approach already built and verified, rather than migrating to a native uv project. Removed the abandoned scaffold (`backend/pyproject.toml`, `backend/uv.lock`, `backend/.python-version`, `backend/README.md`, `backend/src/`, `backend/.venv`, root `src/`) accordingly.
- Cleaned up `__pycache__` directories generated during verification before finishing.

**Decisions:**
- Summarizer asks Gemini for exactly three things — `title`, `summary_text`, `target_persona` — via a pydantic `response_schema`, not a free-form `metadata` dict. `pointer_uri`, `metadata`, and `timestamp` come from the webhook caller instead: a real ingestion parser extracts those deterministically from the source payload, and letting an LLM invent a deep-link URI risks a hallucinated link reaching a user. This mirrors the build doc's own stated goal of the Supervisor/Worker pattern — "prevents AI hallucination."
- The summarizer prompt explicitly instructs Gemini to preserve urgency markers ("P0", "blocked") and PR references ("PR #402") verbatim in `summary_text` — Phase 2's NBA scorer already scans `summary_text` for exactly these patterns, so this keeps the two phases consistent without duplicating detection logic in the summarizer itself.
- `main.py` now calls `load_dotenv(Path(__file__).parent / ".env")` instead of a bare `load_dotenv()` — the bare form only searches upward from the process's current working directory, which would silently miss `backend/.env` when the server is launched from the repo root (as the documented `uvicorn backend.main:app` command does).
- Kept the webhook route source-agnostic (`SimulatedEvent` with `source`, `raw_text`, `pointer_uri`, `metadata`, `timestamp`) rather than writing per-source parsers for GitHub/Jira/Slack/GMeet payload shapes — the build doc's Phase 3 scope is "simulated" ingestion via static JSON, and real per-provider payload parsing is a natural Phase-5-and-beyond concern, not implied by anything phases 1–4 ask for.
- Did not delete or silently repurpose the discovered `uv init` scaffold — asked the user first, since it represented their own unlogged work and the choice (requirements.txt vs. native uv project) has real, lasting structural consequences.

**Verification:** Full real-process run, not just unit-level: `uv venv` + `uv pip install -r backend/requirements.txt` executed for real from a clean state; server started with `uvicorn backend.main:app`; `/health` and `/api/dashboard` hit directly; all four `backend/mocks/*.json` posted through `/webhooks/simulate` (Gemini call stubbed, everything else real) and both persona dashboards confirmed to show only their own chunks, correctly scored and sorted (e.g. the Slack client-escalation chunk hit the 100 cap via urgency + recency + cross-platform bonuses stacking; the GMeet standup chunk with no urgency signal scored 65 from recency alone). No automated test suite exists yet (not requested).

**Unfinished / next steps:** Phase 4 (Next.js frontend: Velocity Timeline, PR Diff Card, Blocker Alerts, NBA Queue with Action Chips) remains — the last phase in the build doc. Next session should confirm Phase 4 scope with the user, read `PERSONA.md` first, and build components that consume `DashboardPayload` directly (see `frontend/src/types` target in the monorepo layout — TS interfaces mirroring `backend/models/schemas.py` haven't been written yet). The real Gemini call path has never been hit live in this environment — worth the user doing one real (non-stubbed) `POST /webhooks/simulate` themselves after setting up `backend/.env`, to catch anything a stub can't (auth errors, actual model output shape drift, latency).

**Commit:** _(record hash here once committed)_
