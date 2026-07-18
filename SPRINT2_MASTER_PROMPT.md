# SPRINT 2 MASTER PROMPT — Close the Gaps, Make It Work (LearnForge / Compass)

> **How to use:** Save in repo root. Open Claude Code in the repo and paste:
> *"Read SPRINT2_MASTER_PROMPT.md in full, then CONTEXT.md. Execute §1–§6 in order. Obey §0 exactly — nothing is 'done' until the harness in §5 proves it. Start with §1."*

---

## §0 — RULES (the last sprint broke these — do not repeat)

Sprint 1 created `auth.py` but wired it into **zero** endpoints; added export libraries but built **no** export endpoint; and claimed `TODO.md` was corrected while the counts never moved. That is the failure this sprint eliminates.

1. **"Done" = a running server produced the correct result.** Not "file exists," not "function defined," not "compiles." Every task below ends with a command in the §5 harness that must print a PASS. If you cannot produce the PASS line, the task is NOT done — say so.
2. **No fail-open security.** Auth that lets requests through when config is missing is worse than no auth, because it looks safe. Missing/invalid token = rejected, always.
3. **Touch only what's listed.** This is a surgical sprint on an existing, mostly-working repo. Do not refactor unrelated code, rename files, or restructure folders.
4. **One task → run → prove → commit.** Commit messages state the evidence, e.g. `feat(export): /api/artifacts/{id}/export returns valid pptx — harness PASS`.
5. **After all phases, rewrite `TODO.md` and `VERIFICATION.md` to match reality** — real checkbox counts, real evidence lines. If a box isn't proven by the harness, it stays unchecked.

**Target:** the existing system works end-to-end at 90–100% — every backend route requires a valid token, users can only touch their own data, every generated artifact downloads as a real file, and one command (`§5`) proves it all.

---

## §1 — ENFORCE AUTH ON EVERY PROTECTED ROUTE (the biggest hole)

Today `agent/auth.py` defines `verify_user` / `get_current_user`, but grep finds them in **no endpoint**. The entire API is open. Fix the dependency, then apply it everywhere.

### 1.1 Fix `agent/auth.py` — remove the fail-open bypass
- Current `verify_user` returns a fake `{"id": "local-dev-user"}` when Supabase env vars are absent. **Delete that branch.** If Supabase isn't configured, that is a server misconfiguration → raise `HTTPException(500, "Auth not configured")`, never admit the request.
- Keep verification real: extract the Bearer token, call `sb.auth.get_user(token)`, reject `401` on missing/invalid/expired. Return the user object (must expose `.id`).
- Add a helper `def user_owns_session(user_id: str, session_id: str) -> bool` that queries Supabase `sessions` and returns whether that session's `user_id` matches (or the user is the teacher of that class). Use it for ownership checks below.

### 1.2 Apply `get_current_user` to every non-public route
Add `user = Depends(get_current_user)` to the signatures of:
- `main.py` → `chat_stream` (POST `/api/chat/stream`)
- `routers/messages.py` → `get_messages`
- `routers/memory.py` → `get_topics_in_session`, `get_sessions_for_topic`, `get_history`, `get_weakness`
- `routers/curriculum.py` → `upload_curriculum`, `list_curriculum_files`
- the new export route in §3
- quiz **admin/results** routes that expose a teacher's data

**Public routes stay public (by design):** the student quiz-answer flow under `/api/quiz/{token}` (get quiz + submit answer). These must NOT require login, but must still validate the token maps to a real quiz and rate-limit submissions (§4).

### 1.3 Enforce ownership, not just authentication
Authentication alone still lets user A read user B's session by guessing an ID. In each protected handler that takes a `session_id` or `user_id`, after auth:
- Derive the identity from the **token** (`user.id`), never trust a `user_id` sent in the query/body for authorization decisions. In `routers/memory.py`, `get_weakness`/`get_history` currently take `user_id` as a query param — switch them to use `user.id` from the token and ignore/deprecate the query param.
- For `session_id`-based routes (`chat_stream`, `get_messages`, memory topic/session lookups), call `user_owns_session(user.id, session_id)`; if false, raise `403`.

### 1.4 Frontend must send the token
The web app calls the API with bare `fetch` (e.g. `ChatUI.tsx` → `/api/chat/stream`, and the curriculum/progress/topics pages). Add the Supabase access token to every API call:
- Get it via the Supabase client session (`supabase.auth.getSession()` → `session.access_token`) and set `Authorization: Bearer <token>` on each `fetch`/EventSource-style request.
- Create one small helper (e.g. `apps/web/src/lib/api.ts` with an `authedFetch(path, init)`) and route all API calls through it so no call ships without a token.

**§1 exit (harness proves each):**
- [ ] Any protected route without a token → `401`.
- [ ] Valid token but another user's `session_id` → `403`.
- [ ] Missing Supabase config → `500` at the auth layer, never a silent pass.
- [ ] The web app's chat, curriculum, progress, and topics calls all include `Authorization: Bearer`.

---

## §2 — MAKE THE COMPOSER EMIT DOWNLOADABLE ARTIFACTS

`composer.py` normalizes artifacts and returns them; `main.py` streams typed events (`token`, later `artifact`). But slides/script artifacts never carry a `download_url`, so the frontend's existing download `<a>` (ArtifactRenderer.tsx ~line 346, fires only `if (data.download_url)`) never lights up.

- In `composer_node`, for every artifact of type `slides | script | worksheet | flashcards | research_brief | resource_card`, attach `art["download_url"] = f"/api/artifacts/{art['id']}/export?format=..."` with a sensible default format per type (slides→pptx, script/worksheet→docx, flashcards→csv, briefs/cards→pdf).
- Persist each artifact (id, type, content, session_id, owner) to Supabase `artifacts` so the export endpoint in §3 can fetch it by id. Keep it non-fatal.
- Ensure `main.py` forwards a final SSE event `{"type":"artifact","data": <artifact>}` for each artifact after the token stream (verify the event generator actually yields these — add it if missing).

**§2 exit:**
- [ ] After a W-A-S turn, the SSE stream contains two `artifact` events (slides + script), each with an `id` and a `download_url`.
- [ ] Those artifacts exist as rows in Supabase `artifacts`.

---

## §3 — BUILD THE REAL EXPORT ENGINE (libs are installed but unused)

`python-docx`, `python-pptx`, `genanki` are in `pyproject.toml`. `python-pptx`'s `Presentation()` is called **nowhere**. Build the endpoint.

### 3.1 New router `routers/export.py`, mounted in `main.py`
`GET /api/artifacts/{artifact_id}/export?format=pptx|docx|pdf|csv` — **auth-protected + ownership-checked** (only the artifact's owner may export it):
- Fetch the artifact from Supabase `artifacts` by id; `404` if absent, `403` if not owned.
- **pptx** (`python-pptx`): parse the slides markdown (split on `---` / `## Slide`), one slide per section, title + body. Return a real `.pptx`.
- **docx** (`python-docx`): render script/worksheet markdown → headings + paragraphs into a real `.docx`.
- **pdf** (`weasyprint` if it builds on the target OS; else `reportlab` or render markdown→HTML→PDF via a pure-python fallback): return a real `.pdf`. If the chosen PDF lib can't install cleanly, log the decision in `DECISIONS.md` and ship docx+pptx+csv, with pdf falling back to docx — but do not silently skip.
- **csv** (flashcards): Anki-importable `front,back` CSV. Also keep the existing `.apkg` genanki path working.
- Stream the file back with correct `Content-Type` and `Content-Disposition: attachment; filename=...`. Write to the Supabase `exports` bucket if available; otherwise stream from memory.

### 3.2 Frontend export bar
In `ArtifactRenderer.tsx`, add an export bar to every artifact card: buttons for the formats valid for that type (slides→PPTX/PDF, script→DOCX/PDF, flashcards→CSV/Anki), each hitting the `download_url` with the chosen `?format=`, sent through `authedFetch` so the token rides along. Keep the existing edit↔preview behavior; nothing auto-publishes.

**§3 exit:**
- [ ] `GET /api/artifacts/{id}/export?format=pptx` returns bytes that open as a valid PowerPoint (harness opens it with `python-pptx` and asserts slide count > 0).
- [ ] `?format=docx` opens as a valid Word doc (`python-docx` reads paragraphs).
- [ ] Export without a token → `401`; export of someone else's artifact → `403`.

---

## §4 — LOCK THE PUBLIC QUIZ PATH (it must stay public but safe)

The student answer flow is intentionally no-auth. Keep it usable, make it safe:
- Validate `{token}` maps to a real quiz row; `404` otherwise.
- Rate-limit submissions per IP (and per token) — a simple in-memory or Postgres counter is fine — to stop spam/ballot-stuffing.
- Cap `respondent_name` and answer payload sizes; reject oversized/malformed bodies `400`.
- Never leak other respondents' data from the public endpoints; only the teacher's authed results route returns the full response set.

**§4 exit:**
- [ ] Answering with a valid token works with no login.
- [ ] A bogus token → `404`; a flood of submissions → throttled; oversized name/body → `400`.
- [ ] The public endpoints never return other students' answers.

---

## §5 — VERIFICATION HARNESS (this is how "done" is proven)

Create `apps/api/scripts/harness.py` — a runnable end-to-end check that boots against a running server and prints `PASS`/`FAIL` per check. It must cover, at minimum:

1. **Boot:** server responds `200` on `/api/health`.
2. **Auth wall:** `POST /api/chat/stream`, `GET /api/messages/{id}`, `GET /memory/weakness`, curriculum upload, and export — each returns `401` with no token.
3. **Ownership:** with user A's token, accessing user B's `session_id` → `403`.
4. **Fail-closed:** with Supabase env unset, the auth layer returns `500`/`401`, never admits.
5. **W-A-S gate:** calling W-A-S with no `lecture_flow` returns the "run Lecture Flow first" guidance and produces **no** script artifact; after a Lecture Flow, W-A-S produces slides + script, and the script contains the markers `WEAK`, `AVERAGE`, `STRONG` in that order.
6. **Persistence:** a value set on turn 1 of a session is present on turn 2 (checkpointer works).
7. **Export:** export the script artifact as docx and the slides as pptx; assert both are valid, non-empty files (open them with `python-docx` / `python-pptx`).
8. **Public quiz:** create a quiz, answer via token with no auth (PASS), answer with a bogus token (404), flood → throttled.
9. **Graceful degradation:** with Qdrant/Tavily down, a normal chat turn still completes (labeled fallback, no 500).

Add an npm/uv script alias so it runs with one command. Provide a stub-token mode (or a seeded test user) so the harness can run without a live browser login. Paste the full PASS/FAIL transcript into `VERIFICATION.md`.

**§5 exit:**
- [ ] `python scripts/harness.py` (or the aliased command) runs and prints every check with PASS.
- [ ] The transcript is pasted into `VERIFICATION.md` under a `## Sprint 2` section.

---

## §6 — RECONCILE THE MAP

- Rewrite `TODO.md` so checkbox states match the harness. Anything not proven by §5 is unchecked. The counts **must** change if reality changed — if they don't, you haven't corrected it.
- Append a `## Sprint 2` section to `DECISIONS.md` for any judgment calls (e.g. PDF library choice, deprecated `user_id` query params).
- Update `README.md` run steps if any command changed (new export route, harness command, required env for auth).

**§6 exit:**
- [ ] `TODO.md` counts reflect the new reality and every checked box has a §5 PASS behind it.
- [ ] `DECISIONS.md` and `README.md` updated.

---

## §7 — ORDER & ACCEPTANCE

Do it in order: **§1 → §2 → §3 → §4 → §5 → §6.** Security (§1) also applies to the routes you build in §3/§4 — never leave a new unauthenticated route behind.

**Final acceptance (the system is 90–100% working when all are true):**
1. Every protected endpoint 401s without a token and 403s across users; auth fails closed.
2. Faculty: Lecture Flow → W-A-S (gated, WEAK→AVERAGE→STRONG) → **download real PPTX + DOCX**.
3. Student quiz link works with no login; abuse is throttled; no data leaks.
4. State persists across turns; app degrades gracefully with services down.
5. `scripts/harness.py` prints all-PASS and the transcript is in `VERIFICATION.md`.
6. `TODO.md` counts match reality.

Work one task at a time: run → prove with the harness → commit. After each phase, print a one-paragraph summary and continue. If any exit criterion can't be met, stop and report exactly what blocks you rather than marking it done.

**Begin with §1.1 now.**
