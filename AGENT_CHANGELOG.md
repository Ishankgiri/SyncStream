# SyncStream — Agent Changelog

This is the persistent handoff document between AI work sessions on this project. Read the **Current State** section before making any changes. Update this file before every commit — it should let an agent with zero conversation history pick up safely.

**Before writing or editing any code, read [`PERSONA.md`](PERSONA.md)** — the project's coding standard (comment philosophy, how much abstraction is appropriate, what "clean" means here). This changelog tracks *what* was built and *why*; `PERSONA.md` governs *how* it should be written. Apply it every session, not just the one it was written in.

Keep this file compact: a maintained "Current State" snapshot at the top, plus append-only session history below. Do not let it become a full transcript.

---

## Current State

**Project:** SyncStream — dual-persona, multi-agent project intelligence copilot (Developer vs. Product Manager briefings) built on a federated-retrieval / chunked-caching architecture. Full product/architecture spec lives in the original build doc (Google AI Builder Cup submission); `README.md` carries a condensed version.

**Phase:** Phase 2 complete. Backend now runs end-to-end against an in-memory chunk store: `GET /api/dashboard` invokes the LangGraph and returns a real `DashboardPayload`. No ingestion pipeline (Phase 3) or frontend (Phase 4) yet, so the store is empty until chunks are added manually or via a future webhook route.

**Repo contents right now:**
- `backend/models/schemas.py` — `PersonaType`, `EventSource`, `ContextChunk`, `ActionItem`, `DashboardPayload` (pydantic v2, unchanged since Phase 1).
- `backend/requirements.txt` — pins verified against what actually installs today (Phase 1's guessed pins were stale): fastapi 0.141.1, uvicorn 0.53.0, pydantic 2.13.5, langgraph 1.2.12, langchain-core 1.6.4, python-dotenv 1.2.3, google-cloud-aiplatform 1.75.0 (still unused — Phase 3).
- `backend/data_pipeline/vector_store.py` — in-memory chunk store: `add_chunk`, `query_chunks_by_persona(persona, since=None)`. Stands in for Vertex AI Vector Search; Phase 3 wires ingestion to `add_chunk`, and the backing store can later be swapped for real Vertex calls without touching callers.
- `backend/agents/state.py` — `GraphState` TypedDict (`user_id`, `persona`, `query_time_range`, `retrieved_chunks`, `final_payload`), shared by all nodes.
- `backend/agents/master_router.py` — `master_router_node` (pass-through entry node) + `route_by_persona` (conditional-edge function: developer → engineering_worker, else → business_worker).
- `backend/agents/worker_eng.py`, `backend/agents/worker_biz.py` — each pulls chunks scoped to exactly one persona via `vector_store.query_chunks_by_persona`. This is what enforces the "no persona bleed" constraint structurally.
- `backend/agents/graph.py` — wires the above into a compiled LangGraph (`dashboard_graph`): `START → master_router → (engineering_worker | business_worker) → build_dashboard → END`. `build_dashboard` calls `nba_scorer.build_nba_queue` and assembles the final `DashboardPayload`.
- `backend/engine/nba_scorer.py` — `score_chunk` (base 50; +30 urgency keyword; +15 if <2h old; +20 if a non-GitHub chunk references a `PR #<n>`; capped at 100) and `build_nba_queue` (scores + sorts descending).
- `backend/main.py` — FastAPI app, CORS open to `localhost:3000`, `GET /health`, `GET /api/dashboard?user_id&persona&since`.
- `PERSONA.md` — coding standard (comment philosophy, proportionate implementation). Read before writing code.
- `frontend/package.json` — unchanged since Phase 1 (Next.js 14, React 18, TS, Tailwind deps only, no app code yet).
- `.gitignore`, `README.md`, `AGENT_CHANGELOG.md`.

**Active work:** None in progress. Waiting on the user to confirm kickoff for **Phase 3** (simulated webhook ingestion + Gemini chunking, writing into `vector_store.add_chunk`).

**Known issues / traps:**
- The vector store is in-memory and process-local — it resets on every server restart and holds nothing until Phase 3's ingestion route exists. `GET /api/dashboard` against a fresh process returns an empty `nba_queue`; that's correct behavior, not a bug.
- Build doc explicitly forbids live API scraping at runtime; all retrieval must go through pre-chunked summaries in the vector store. Do not let any agent implementation call GitHub/Jira/etc. APIs synchronously during a dashboard request. (Phase 2 respects this: workers only ever call `vector_store.query_chunks_by_persona`.)
- Build doc explicitly forbids persona data bleed — enforced in Phase 2 by construction, since each worker only ever queries its own persona's chunks. The one deliberate crack in that wall is the NBA scorer's cross-platform bonus, which inspects a chunk's own text for a PR reference — it never reads the other persona's chunk set.
- MVP scope: GitHub is the only *live* integration; Jira and Slack are mocked via static JSON; Google Meet transcripts are simulated (local JSON / Drive API), not live meeting ingestion. None of that ingestion exists yet — Phase 3.
- `httpx` was used transiently (in a throwaway venv, not committed) to smoke-test `TestClient`; it is not in `requirements.txt` and isn't needed until an actual test suite is set up.

**Next steps:** Ask the user to confirm before starting Phase 3 (per the build doc's own execution protocol, phases should be done one at a time, not all at once).

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
