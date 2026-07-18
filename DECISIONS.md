# DECISIONS.md — LearnForge Engineering Decisions Log
> Every judgment call, spec deviation, or design decision is logged here with rationale.

---

## 2026-07-18 — Phase 1 Recovery Audit

### DEC-001: gate_wf removed
- **Claim in TODO.md:** `gate_wf` was checked as done.
- **Reality:** `gate_wf.py` implements a "learner progress gate" that hijacks all learner chat if `lecture_flow.active_lesson == True`. This feature **does not appear in CONTEXT.md**.
- **Decision:** Removed `gate_wf` from the graph entirely. Deleted the errant learner-hijack routing logic from `router.py`. `gate_wf.py` file retained on disk as archive.
- **Spec reference:** CONTEXT.md does not mention a gate workflow. RECOVERY_MASTER_PROMPT.md §2.2 explicitly says "Remove it; `gate_wf` is not a real feature."

### DEC-002: Checkpointer deferred to Phase 2
- **Issue:** Graph compiles with no checkpointer; all state dies every turn.
- **Decision:** Noted in `graph.py` with a TODO comment. Full PostgresSaver wiring addressed in Phase 2.
- **Impact:** lecture_flow does NOT survive across turns until Phase 2.

### DEC-003: weasyprint excluded from pyproject.toml
- **Issue:** weasyprint has heavy system-level GTK dependencies that cannot be installed on Windows.
- **Decision:** Excluded. PDF export uses DOCX via python-docx. README notes "PDF export requires Linux/Docker."

### DEC-004: Semantic Scholar deferred to Phase 6
- **Decision:** Marked as not done in AUDIT.md. Will be added in Phase 6.

### DEC-005: "Socratic" chip removed (not in spec)
- **Decision:** Remove any "Socratic" chip from frontend chip arrays. CONTEXT.md does not include it.

### DEC-006: lecture_flow structured dict format
- **Old code:** Set `{"active_lesson": True, "current_stage": "Intro"}` — useless for W-A-S.
- **Decision:** `lecture_wf` now parses `<flow_json>` from LLM output and sets `lecture_flow` to `{topic, class_level, hook, segments[], close}`. W-A-S gate checks `lecture_flow.get("segments")`.

### DEC-007: CORS wildcard replaced with env-var origin list
- **Decision:** Origin restricted to `WEB_ORIGIN` env var (defaults to `http://localhost:3000`).

---

## 2026-07-18 — Final Sprint, Part A1 (first real harness run)

### DEC-008: Gemini model switched from `gemini-2.0-flash` to `gemini-flash-latest`
- **Issue:** `gemini-2.0-flash` returns `429 RESOURCE_EXHAUSTED` with `limit: 0` on every configured key (primary + 2 fallbacks) — this project's free tier has no quota for that specific model string anymore.
- **Decision:** `agent/llm.py` now requests `gemini-flash-latest`, confirmed working (~2s response) on the same primary key.
- **Impact:** All LLM-backed nodes. No prompt/behavior change, model alias only.

### DEC-009: `max_retries` reduced from 20 to 2, explicit `timeout=20` added
- **Issue:** Google's SDK backs off up to 60s between attempts; `max_retries=20` could hang up to ~15 minutes on a single rate-limited key, and up to ~45 minutes once chained through both fallback keys via `with_fallbacks`. This is what made turns "hang" rather than fail.
- **Decision:** `agent/llm.py` now uses `max_retries=2, timeout=20` per key. A stuck key now fails over to the next key in seconds instead of stalling the chat turn.
- **Impact:** Faster, cleaner failure under rate limiting. No behavior change when keys are healthy.

### DEC-010: `response.content` → `response.text` in all artifact-parsing nodes
- **Issue:** The installed langchain-google-genai version returns `AIMessage.content` as a list of content blocks, not a plain string. Every `"<artifact...>" in response.content` check in `flashcards_wf.py`, `worksheet_wf.py`, `quiz_wf.py`, `was_wf.py`, `diagrams_wf.py`, `research_wf.py`, `resource_wf.py`, `lecture_wf.py`, and the topic-extraction call in `memory_writer.py` silently evaluated `False` — no artifacts were ever produced, no error was ever raised. This means every "done" checkbox in TODO.md for artifact-producing chips (Phases 4–7) was **not actually functioning** at the time it was checked off, despite passing manual review.
- **Decision:** Switched all text-parsing reads to `response.text` (langchain_core's built-in content-block-aware accessor). Assignments (`response.content = <plain string>`) were left as-is — those are writes, not reads, and are unaffected.
- **Impact:** This is the single highest-impact fix in the sprint — it silently un-breaks the entire artifact pipeline (flashcards, worksheets, quizzes, W-A-S script+slides, diagrams, research briefs, resource cards, lecture flow) and topic extraction in the memory backbone. It also fixed a latent crash in `flashcards_wf.py` (`response.content.replace(...)` on a list would have raised `AttributeError` the moment the code path was ever reachable).

### DEC-011: CSV export rewritten to parse artifact JSON instead of naive line-splitting
- **Issue:** `routers/export.py::export_csv` split every line on the first `:` — a heuristic for a "Term: definition" markdown format that flashcards never actually use. Flashcards are single-line JSON inside `<artifact type="flashcards">`, so the old code produced one garbage row per export instead of one row per card. This bug was masked because `prove_sprint2.py`'s original assertion only checked that the substrings `"Front"` and `"Back"` appeared anywhere in the CSV — true even for the garbage output.
- **Decision:** `export_csv` now extracts the JSON payload from inside the `<artifact>` tag and writes one `Front,Back` row per card, falling back to the old line-splitting heuristic only when the content isn't parseable JSON.
- **Impact:** Anki/CSV flashcard exports are now actually usable output, not one malformed row.

### DEC-012: Wikimedia image search now sends a `User-Agent` header
- **Issue:** `en.wikipedia.org/w/api.php` now enforces Wikimedia's robot policy and rejects any request without an identifying `User-Agent` — every call returned a plain-text 403 body, which crashed `res.json()`. This meant the Wikimedia fallback was permanently dead (silently swallowed by the surrounding try/except), and every diagram request was actually running on the DuckDuckGo-only path.
- **Decision:** `agent/tools/images.py` now sends `User-Agent: LearnForge/1.0 (...)` and calls `res.raise_for_status()` before parsing JSON, so a future policy change fails loudly (logged) instead of throwing an opaque JSON-decode error.
- **Impact:** Wikimedia is a real fallback source again.

### DEC-013: Semantic Scholar search gets one bounded retry, honors `Retry-After`
- **Issue:** The unauthenticated Semantic Scholar endpoint shares one global rate-limit pool across all callers and was observed 429'ing consistently during this sprint's testing (external, not caused by this app specifically).
- **Decision:** `search_semantic_scholar` now retries once, waiting `Retry-After` (capped at 15s) before giving up and returning `[]`. Still fully non-fatal — no behavior change to callers on success or final failure, just a better chance of getting real results under transient load.
- **Impact:** `prove_sprint2.py`'s Semantic Scholar check now distinguishes "our code is broken" from "the free third-party quota is tight right now" — it probes the endpoint first and treats a live 429 as an expected, non-fatal condition (verifying graceful `[]` degradation) rather than failing the whole harness on something outside this codebase's control.

### DEC-014: Quiz sharing was completely non-functional — fixed the `quizzes.artifact_id` FK violation
- **Issue:** `quiz_wf_node` inserted `{"artifact_id": token, "share_token": token, ...}` where `token` is a freshly-generated UUID for the public share link — not a real `artifacts.id`. `quizzes.artifact_id` has a hard FK to `artifacts(id)`. Confirmed empirically (`POST /rest/v1/quizzes` with a fabricated `artifact_id` → `409 / 23503 foreign key violation`). The insert was wrapped in a bare `try/except: print(...)`, so this failed **silently, every single time** — no quiz created via the faculty Quiz chip ever actually persisted. The share link rendered in the chat UI 404'd for anyone who opened it (`GET /api/quiz/{token}`).
- **Decision:** `quiz_wf_node` now generates one `art_id` up front, inserts the `artifacts` row itself (`type="quiz"`) *before* inserting the `quizzes` row referencing that same `art_id` — satisfying the FK at insert time, since `composer_node` (which normally persists artifacts) only runs *after* this node returns. `composer.py`'s artifact persistence changed from `.insert()` to `.upsert(..., on_conflict="id")` so composer's now-redundant later write on the same id is idempotent instead of a swallowed duplicate-key error.
- **Impact:** This is the second highest-impact fix in the sprint after DEC-010 — the shareable-quiz flagship feature (Phase 5, checked off as done) had never actually worked.

## 2026-07-18 — Final Sprint, Part B

### DEC-024: RLS is already live on the production Supabase project — with zero policies, actively breaking real reads
- **Found while verifying the rebuilt public quiz page (C2.7):** a freshly-created quiz's share link returned "Quiz not found" even though the row demonstrably existed (confirmed via the service key). Investigated further and confirmed precisely: querying `sessions` for a real, currently-logged-in user's own `user_id`, using that user's own valid JWT + the anon key (exactly what `@/utils/supabase/server`'s `createClient()` does), returns `[]`. The identical query via the service key returns their real row. Tested on both `quizzes` (anon, unfiltered) and `sessions` (authenticated owner, filtered to their own rows) — both `200 []`.
- **What this means:** contrary to DEC-016's assessment ("RLS not yet applied"), Postgres RLS *is* enabled on at least `sessions` and `quizzes` in the live project — almost certainly on all tables, likely via Supabase's dashboard "Security Advisor" prompt, which nags project owners to enable RLS project-wide with a single click and does **not** add any policies. RLS with zero policies is default-deny for everyone except the service role — worse than RLS being off, because it silently breaks legitimate access without erroring.
- **Real-world impact (live, right now, independent of anything built this sprint):** every direct-Supabase-from-the-frontend read is broken — the sidebar's session list (independent of the `created_at` column-name bug also fixed this session, DEC-018), the public quiz page (no respondent has ever been able to open a quiz link — the anon key gets zero rows), and the Progress/Topics/Curriculum pages' direct reads. The FastAPI backend is unaffected (it exclusively uses `SUPABASE_SERVICE_KEY`, which bypasses RLS).
- **Decision:** flagged to the user immediately as a live-functionality bug, not a hardening backlog item — the previously-deferred A2 migration (`apps/api/db/migrations/002_rls_and_artifact_types.sql`) is the exact fix (it adds the missing policies), so no new code was needed, only re-prioritizing getting it applied. User chose to run it via the Supabase SQL Editor directly. See the entry below once applied for the re-verification result.

### DEC-022: Fixed a real token-leak bug found while visually verifying the new artifact panel (Part C)
- **Issue:** `main.py`'s `/api/chat/stream` forwarded `on_chat_model_stream` tokens from *any* chat-model call in the graph to the client, unfiltered. `astream_events` fires this event for every LLM invocation, including `memory_writer`'s internal topic-extraction call — which is never meant to be user-facing. Confirmed empirically (`agent/graph.py` probe): both the response-generating workflow node and `memory_writer` show up as `event["metadata"]["langgraph_node"]` on `on_chat_model_stream` events. In the browser, this meant every real response was followed by memory_writer's raw topic-extraction JSON leaking into the same message bubble (e.g. a flashcards answer ending in `[{"name": "Water Cycle", "parent": null}, ...]`) — visible on **every single turn**, not an edge case.
- **Decision:** `main.py` now checks `event["metadata"]["langgraph_node"]` and skips forwarding tokens from `memory_writer`.
- **Found via:** live Playwright verification of the new `ArtifactPanel`/`ArtifactCard` components (Part C2.3) — driving a real login + chat turn in a browser, not just reading code, is what surfaced this; `next tsc --noEmit` alone would never have caught it.

### DEC-023: Groq fallback doesn't reliably follow the `<artifact type="...">` output-format instruction (known limitation, not fixed)
- **Found:** while live-testing the artifact panel with Gemini still quota-exhausted (forcing the Groq fallback from DEC-021), a flashcards request returned well-formed prose but **not** wrapped in `<artifact type="flashcards">...</artifact>` as `flashcards_wf.py`'s system prompt requires. Every artifact-producing workflow checks for that exact tag before building a structured artifact (the same `if "<artifact...>" in text` pattern from DEC-010) — when the model doesn't emit it, the check silently evaluates `False` and no artifact is created, same failure *shape* as DEC-010 but a different *cause* (model instruction-following, not a content-format API change).
- **Not fixed this sprint:** making every artifact-producing workflow robustly parse non-tagged fallback output (or switching Groq calls to a structured/JSON response mode) is real work, closer to Part D's "model routing" scope than Part C's UI pass, and this specific failure mode only triggers when Gemini is *also* exhausted — an unusual condition from this sprint's heavy testing, not steady-state usage.
- **Impact if hit in production:** under sustained Gemini quota exhaustion, artifact-producing chips would silently degrade to plain prose with no downloadable artifact, no error shown to the user. Flagged here so it isn't rediscovered as a surprise later.

### DEC-020: B3 drill-down parent detection reads Postgres, not `state["topics_touched"]`
- **Issue found while testing B3:** `main.py`'s `/api/chat/stream` builds a fresh `inputs` dict on every single turn that explicitly includes `"topics_touched": []`. Since this key has no LangGraph reducer annotation (unlike `messages`, which uses `add_messages`), supplying an explicit value in `inputs` overwrites whatever the SQLite checkpointer persisted from the previous turn. **`state["topics_touched"]` never actually survives across turns** — every node that reads it mid-session sees `[]`, no matter what happened earlier in the same session. (Everything that reads it — the just-added B2 nudge, `context_loader`'s weakness injection — only reads it *within the same turn* after `memory_writer` just set it, so this specific bug didn't visibly break those; it would have silently broken any future feature that assumed cross-turn persistence, exactly as it broke my first pass at B3.)
- **Decision:** Did **not** touch `main.py`'s reset behavior — that's a wider-blast-radius change to the core streaming endpoint's state-init behavior for every turn, out of scope for a targeted B3 fix and risky to change without full regression coverage across every workflow. Instead, `memory_writer.py` now has `_prior_topics_for_session(sb, session_id)`, which reads already-recorded topics for this session directly from `user_topic_events`/`topics` in Postgres — durable, correctly session-scoped, unaffected by the state-reset bug. B3's parent-detection prompt uses this instead of `state.get("topics_touched")`.
- **Flag for a future sprint:** if `topics_touched` is ever needed as true cross-turn *state* (not just DB-backed), `main.py` needs either an `add`-style reducer on that field or to stop overwriting it in `inputs` on every turn.

### DEC-021: The 3-key Gemini fallback chain shares one quota pool — confirmed empirically, resolved with a Groq tier
- **Found while testing B2/B3:** mid-session, every configured key (`GOOGLE_API_KEY`, `GEMINI_FALLBACK_API_KEY`, `GEMINI_FALLBACK_API_KEY_2`) started returning `429 RESOURCE_EXHAUSTED` for `gemini-flash-latest` (resolves to `gemini-3.5-flash`, quota `20` requests). Probed all three keys directly and independently: **all three failed with the identical quota-exhausted error**, confirming they are not independent fallback capacity — likely three API keys under the same Google Cloud project/billing account, sharing one pool.
- **Impact:** DEC-009's "resilient 3-layer LLM factory" protects against a single key being transiently unhealthy, but provided **no actual protection against quota exhaustion** — the failure mode that matters most on a free tier this small (20 req/day is trivial to exhaust while testing).
- **Resolution:** user supplied two Groq API keys. `agent/llm.py`'s fallback chain now appends `ChatGroq(model="llama-3.3-70b-versatile")` for both as a final tier after the 3 (shared-quota) Gemini keys — a genuinely independent provider/quota, not just another key on the same pool. Verified directly: with all 3 Gemini keys still exhausted, `get_llm().invoke(...)` now falls through and returns a real response via Groq in ~7s. Keys added to `apps/api/.env` (gitignored, confirmed via `git check-ignore` before writing) as `GROQ_API_KEY`/`GROQ_FALLBACK_API_KEY`.
- **Consequence for this sprint:** unblocked full live re-verification of B2/B3 (see VERIFICATION.md) and the complete 13-check harness run.

### DEC-018: Sidebar "Recent Chats" was silently empty for every user — `.order('created_at')` on a table with no such column
- **Issue:** `faculty/layout.tsx` and `learn/layout.tsx` both queried `sessions.select('id, title').order('created_at', ...)`, but `sessions` has `started_at`, not `created_at` (per `db/schema.sql`). Confirmed empirically: `GET .../sessions?order=created_at.desc` returns `400 { "code": "42703", "message": "column sessions.created_at does not exist" }`. Both layouts destructure only `{ data }` (ignore `error`), so on this 400 `data` is `null` and `sessions = data || []` silently becomes `[]`. **The sidebar's recent-chats list has never shown anything, for any user, ever.**
- **Decision:** Fixed both layouts to `.order('started_at', ...)`. Found and fixed while wiring B1 (session summarizer), since both layouts needed a `summary` column added to the same query anyway.
- **Impact:** Sidebar now actually lists sessions. Unrelated to B1 functionally, but same files, same commit.

### DEC-019: Session summarizer trigger lives in a new backend endpoint, not the Next.js server layouts
- **Spec:** "run it lazily when a session is next listed."
- **Issue:** The faculty/learner layouts are React Server Components that read `sessions` directly from Supabase with the user's own session (no FastAPI round-trip today). Calling the FastAPI backend from there would mean re-deriving the access token server-side and adding a new pattern; the existing `/learn/topics` page already calls the FastAPI backend via `authedFetch` for topic pills, so it was the natural, already-established integration point.
- **Decision:** Added `GET /api/memory/sessions/mine` (routers/memory.py) — lists the user's sessions and, for each one crossing the eligibility bar (>=4 messages, no summary yet), generates and persists a summary via `agent/memory_summarizer.py` before returning. `/learn/topics` now calls this endpoint instead of querying Supabase directly, so visiting that page is the actual trigger point. The sidebar layouts still read `sessions` directly from Supabase (now including `summary`) — they display whatever the topics page (or any other future caller of the new endpoint) already generated, rather than triggering generation themselves.
- **Impact:** Matches the "lazy on listing" spec via the page a learner is actually most likely to open to review past work, without adding a second FastAPI-calling code path to two server layouts. Model used for the summary is Gemini via the existing `agent/llm.py::get_llm()` (not Groq — see DEC-005-area rationale: no `GROQ_API_KEY` is configured in `.env` and the whole codebase already migrated off Groq in commit 9ee56b1c; introducing a second LLM provider for one feature would contradict "touch what's listed, don't refactor").

### DEC-017: Public quiz-submit rate limiting is in-memory, single-process
- **Decision:** `routers/quiz.py` now throttles `/api/quiz/{token}/submit` with two independent in-memory sliding-window counters (10 requests/60s per client IP, 10/60s per quiz token), plus hard caps on `respondent_name` (≤80 chars) and `answers` payload (≤20KB), and manual JSON body validation returning 400 on anything malformed instead of FastAPI's default 422.
- **Why this shape:** matches FINAL_SPRINT_MASTER_PROMPT.md §A3 exactly (per-IP + per-token throttle, explicit input caps, 429 on throttle, 400 on malformed input).
- **Known limitation:** the counters are plain in-process `dict`s — they reset on restart and don't share state across multiple workers/replicas. Fine for the current single-instance deployment; if this ever runs behind multiple processes/instances, the counters need to move to Redis or Postgres so all instances see the same rate-limit state.

### DEC-016: RLS migration written but not yet applied to live Supabase — no DDL credentials available
- **Issue:** `apps/api/.env` has `SUPABASE_URL`/`SUPABASE_ANON_KEY`/`SUPABASE_SERVICE_KEY` — all PostgREST/Auth API credentials. None of them can execute DDL (`ALTER TABLE ... ENABLE ROW LEVEL SECURITY`, `CREATE POLICY`); PostgREST only exposes table-level REST operations. No `DATABASE_URL`/direct Postgres connection string is present, and the Supabase CLI isn't installed/linked in this environment.
- **Decision:** Wrote the full migration to `apps/api/db/migrations/002_rls_and_artifact_types.sql` (also folded into `db/schema.sql` for fresh installs) — RLS enabled + per-table policies exactly per spec, plus the `artifacts.type` CHECK fix from the harness findings above. Not yet applied to the live project; needs either a direct DB connection string or the user running it via the Supabase SQL Editor.
- **Impact:** A2's "RLS live and tested" exit criterion is blocked on this. Migration is ready to run the moment credentials or manual execution are available.

### DEC-015: `user_owns_session` no longer grants blanket access to all faculty accounts
- **Issue:** Found while building the quiz-results-ownership harness check. `agent/auth.py::user_owns_session` had a second branch: if the requesting user's role is `faculty`, return `True` — with **no check that they own the specific session**. This function gates `/api/chat/stream`, `/api/quiz/{token}/results`, and `/api/artifacts/{id}/export`. Net effect: any faculty account could read or write into **any other user's session**, faculty or learner, just by knowing/guessing a session id.
- **Decision:** Removed the blanket faculty bypass. Ownership is now strictly `sessions.user_id == requesting user's id`.
- **Impact:** Closes a real cross-tenant data-access hole in the FastAPI layer itself — independent of and in addition to the RLS work in A2 (RLS protects direct anon-key+JWT access to Supabase; this protects the FastAPI backend, which uses the service key and was the *only* thing standing between users on these three routes).
