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

### DEC-015: `user_owns_session` no longer grants blanket access to all faculty accounts
- **Issue:** Found while building the quiz-results-ownership harness check. `agent/auth.py::user_owns_session` had a second branch: if the requesting user's role is `faculty`, return `True` — with **no check that they own the specific session**. This function gates `/api/chat/stream`, `/api/quiz/{token}/results`, and `/api/artifacts/{id}/export`. Net effect: any faculty account could read or write into **any other user's session**, faculty or learner, just by knowing/guessing a session id.
- **Decision:** Removed the blanket faculty bypass. Ownership is now strictly `sessions.user_id == requesting user's id`.
- **Impact:** Closes a real cross-tenant data-access hole in the FastAPI layer itself — independent of and in addition to the RLS work in A2 (RLS protects direct anon-key+JWT access to Supabase; this protects the FastAPI backend, which uses the service key and was the *only* thing standing between users on these three routes).
