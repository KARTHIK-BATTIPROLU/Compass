# FINAL SPRINT MASTER PROMPT — Complete LearnForge (Features + Beautiful UI + Optimize + Ship)

> **How to use:** Save in repo root. Open Claude Code in the repo and paste:
> *"Read FINAL_SPRINT_MASTER_PROMPT.md in full, then CONTEXT.md. Execute Parts A→E in order, obeying §0. Nothing is 'done' until the harness proves it or a screenshot/artifact shows it. Start with Part A."*

---

## §0 — RULES

The last two sprints proved a pattern: self-contained features get built well; cross-cutting closers (running the harness, reconciling TODO.md) get skipped. `TODO.md` has read **60 checked / 6 unchecked for three sprints straight** while the codebase changed massively underneath it. This sprint ends that.

1. **"Done" = proven.** Backend: a PASS line from the harness. Frontend/UI: the page rendered in a browser (screenshot or described render check) with no console errors. Docs: the diff shows the counts changed.
2. **Run things.** `prove_sprint2.py` exists at the repo root but was never executed — no transcript in `VERIFICATION.md`. Executing the harness is task #1 of this sprint, before any new code.
3. **Touch what's listed; don't refactor working code.** W-A-S, auth, exports, memory, curriculum ingest are working — protect them. Any behavior change to a working feature requires a note in `DECISIONS.md`.
4. **One task → run → prove → commit**, message includes evidence.
5. **UI work is design work, not decoration.** Part C gives a design system; follow it exactly. Every screen you touch must meet the quality floor: responsive to 375px, visible keyboard focus, `prefers-reduced-motion` respected, text contrast ≥ 4.5:1.

**Definition of finished:** harness all-PASS; RLS on; public quiz abuse-proof; the three missing features built (summarizer, end-of-session quiz trigger, drill-down edges); every screen restyled to the Part C system; measurable perf wins from Part D; both apps deployed on free tiers; `demo_script.md` executes cleanly on the deployed URLs; `TODO.md` finally tells the truth.

---

# PART A — PROVE WHAT EXISTS, CLOSE SECURITY (do first, ~half a day)

### A1. Run the harness — for real
- Start the API (`uv run uvicorn main:app --port 8000`) and run `python prove_sprint2.py`. Fix whatever fails until it prints all-PASS. Paste the full transcript into `VERIFICATION.md` under `## Final Sprint — Harness Run 1`.
- Extend the harness with checks for everything added since (Wikimedia image sourcing fallback, Semantic Scholar results present in research/resource output, Anki `.apkg` download, quiz-results ownership 403).

### A2. Enable Row-Level Security (currently OFF — last real security hole)
- `db/schema.sql` has no policies. Add `ALTER TABLE ... ENABLE ROW LEVEL SECURITY` plus per-user policies for every table: `users` (self), `sessions`/`messages`/`artifacts`/`curricula` (owner), `quizzes`/`quiz_responses` (owning teacher; responses insertable via service role from the public path), `topics`/`topic_edges` (readable by all authed users, writable by service role), `user_topic_events`/`weakness_profiles` (self). Apply to the live Supabase project and commit the migration SQL.
- Harness check: with only the anon key and user A's JWT, selecting user B's rows returns empty.

### A3. Lock the public quiz path (still wide open to abuse)
- `routers/quiz.py` has **no rate limiting and no input caps**. Add: per-IP + per-token submission throttle (simple in-memory dict with timestamps is acceptable; note the single-process limitation in `DECISIONS.md`), `respondent_name` ≤ 80 chars, answers payload ≤ 20KB, reject malformed bodies 400, and return 429 with a friendly message when throttled.
- Harness check: 20 rapid submissions → 429; oversized name → 400.

**Part A exit:** harness transcript in VERIFICATION.md, RLS live and tested, quiz abuse checks PASS.

---

# PART B — COMPLETE THE MISSING FEATURES (~1 day)

Three spec features remain unbuilt (the honest unchecked boxes):

### B1. Session summarizer
- New logic (triggered on session close or ~30 min inactivity — a lightweight approach: run it lazily when a session is next listed, if it has ≥4 messages and no summary): Groq generates a 2–3 sentence summary → save to `sessions.summary` → embed into Qdrant `session_chunks`.
- Show the summary as the session subtitle in the Sidebar and on the Sessions/Topics page.

### B2. Learner end-of-session quiz trigger
- The learner's Quiz-Me chip works on demand; the *automatic* wrap-up doesn't exist. Implement: when the learner has ≥5 turns in a session, the composer appends a gentle nudge card ("Ready to test what you covered? →") that, when clicked, fires the quiz chip pre-scoped to `topics_touched`. No auto-generation without the click (nothing auto-publishes).
- Scores flow into the existing weakness pipeline → `/learn/progress` updates.

### B3. Mid-conversation drill-down edges
- In `memory_writer`, when the current turn's extracted topic is a child of a topic touched earlier in the session (ask the extractor to also return `parent` when confident), upsert a `topic_edges` row (`parent → child, relation='subtopic'`). The Topics page then shows a small indented tree instead of a flat list.

**Part B exit:** harness checks — a summarized session shows `sessions.summary`; a 5-turn learner session surfaces the quiz nudge; a drill-down conversation produces a `topic_edges` row and the Topics page renders the hierarchy.

---

# PART C — THE UI OVERHAUL (make it genuinely beautiful, ~1–1.5 days)

The current UI is functional glass-on-gradient but generic — it could be any AI chat app. Rebuild the visual identity around what this product actually is: **a forge for lessons**. The metaphor: raw material (a prompt, a syllabus) goes in; shaped, layered artifacts (flows, scripts, slides, quizzes) come out. Warm light on dark metal — not the default indigo-SaaS glow.

### C1. Design tokens (define once in `globals.css` + `tailwind.config.ts`, use everywhere)
**Palette — "midnight forge":**
- `--bg-deep: #0B0F1A` (near-black blue — the workshop at night)
- `--bg-panel: rgba(20, 26, 43, 0.55)` (glass panels)
- `--ember: #F59E5B` (forge-ember amber — primary accent: active chips, CTAs, progress fills)
- `--ember-hot: #FBBF74` (hover/active state of ember)
- `--steel: #8B9BB4` (secondary text, borders at 25% alpha)
- `--mint-signal: #6EE7B7` (success/mastery only — quiz correct, strong mastery rings)
- Platform tint: faculty screens warm the gradient mesh toward amber; learner screens cool it toward teal — same system, two temperatures, so users always know which door they're in.

**Type:** display = **Fraunces** (a warm, characterful serif for page titles, session headers, artifact titles — used sparingly); body/UI = keep **Geist** (already shipped in the repo); mono = **Geist Mono** for tokens, timings, and quiz codes. Scale: 32/24/18/15/13 with generous line-height on body (1.6).

**Surfaces:** panels `backdrop-blur-xl` + `--bg-panel` + 1px border `--steel/25` + `rounded-2xl`; one soft amber glow shadow reserved **only** for the active artifact and active chips — nothing else glows.

**Signature element (the one memorable thing):** the **W-A-S gradient seam** — a thin 3px vertical bar on every script artifact and every progress element, running mint (weak/foundational) → amber (average) → deep ember (strong). It encodes the product's core idea (layered difficulty) into the visual language. Use it on: script section headers, the W-A-S chip when active, mastery rings, and the landing page hero.

### C2. Screen-by-screen pass (in this order)
1. **Landing (`/`)** — hero as thesis: headline set in Fraunces — "Forge every lesson three ways." beneath it, a live-looking mini artifact card cycling WEAK→AVERAGE→STRONG snippets with the gradient seam; two door cards (Faculty warm / Learner cool) with a short line of real copy each ("Plan, layer, and share your class" / "Learn it, test it, keep it"). No feature-grid boilerplate.
2. **Chat (both platforms)** — messages as quiet glass cards; user right-aligned ember-tinted, agent left neutral; streaming text with a subtle fade-in per token batch; chips bar floats bottom-center as glass pills, active = ember ring + slight lift (Framer Motion spring), and the W-A-S chip carries the seam. Session header shows class/language badges as small steel pills.
3. **Artifact experience** — convert the inline `ArtifactRenderer` into a **slide-in right panel** (Framer Motion `AnimatePresence`, spring, 420–520px, full-height): sticky header (artifact title in Fraunces + type badge), edit↔preview toggle, and the export bar (PPTX/DOCX/CSV/Anki buttons already wired to `download_url`) pinned at the bottom. Slides artifacts render as horizontal slide cards; scripts show the three W-A-S sections with the seam and collapsible headers; keep the 3D flashcard flip.
4. **Progress (`/learn/progress`)** — mastery rings using the seam gradient (ring fill animates on load, respects reduced-motion); weak topics as tappable ember-outline pills that jump into a chat pre-filled with "revisit <topic>".
5. **Topics (`/learn/topics`)** — session timeline down the left (date, Fraunces title, summary subtitle from B1), topic tree from B3 on the right; clicking a topic filters the timeline.
6. **Curriculum (`/faculty/curriculum`)** — drag-drop zone as a glass "anvil" panel with upload progress; uploaded syllabi listed with chunk counts.
7. **Quiz public page (`/q/[token]`)** — mobile-first, one question per screen, big tap targets, ember progress bar, mint check on submit; it will be opened from WhatsApp on phones, design for that.
8. **States everywhere** — glass shimmer skeletons while loading; empty states that invite action ("No sessions yet — start one and it'll appear here"); errors that say what happened and what to do, never a raw message.

### C3. Quality floor (non-negotiable, applies to every screen above)
Responsive to 375px; keyboard focus visible (ember outline); `prefers-reduced-motion` disables the spring/ring animations; contrast ≥4.5:1 (check ember-on-dark text sizes); copy in sentence case, active voice, buttons say what they do ("Download PPTX", not "Export").

**Part C exit:** each of the 8 screens rendered and checked in-browser at desktop + 375px; no console errors; a `## UI Overhaul` note in VERIFICATION.md listing each screen with its check.

---

# PART D — OPTIMIZE (~half a day)

1. **Parallelize W-A-S:** `was_wf` generates slides then script sequentially — run both with `asyncio.gather` (halves the flagship's latency).
2. **Model routing for cost/speed:** keep Gemini for long-form (lecture, W-A-S, research synthesis); move short structured jobs (topic extraction already on Groq, quiz JSON, flashcards) to Groq via the existing `agent/llm.py` helper. Log per-node model choice in Langfuse.
3. **Trim prompt payloads:** cap `curriculum_ctx` to top-5 chunks ≤ 600 tokens each; cap message history sent to LLMs to the last 12 turns + session summary (from B1) — faster, cheaper, and long sessions stop degrading.
4. **Embedding cache:** hash chunk text → skip re-embedding identical chunks on curriculum re-upload.
5. **Frontend:** lazy-load the artifact panel and flashcard components (`next/dynamic`); memoize message list rendering so streaming doesn't re-render the whole thread; ensure `next build` passes with zero type errors.
6. **Checkpoint hygiene:** the SQLite checkpoint files (`checkpoints.db*`) are committed to git — add `apps/api/data/` to `.gitignore`, remove from the index, and add a startup prune of checkpoints older than 14 days.

**Part D exit:** before/after timing for one W-A-S turn recorded in VERIFICATION.md (expect ~2× faster); `next build` clean; checkpoints out of git.

---

# PART E — DEPLOY + DEMO (~half a day)

1. **Deploy:** web → Vercel; API → Render or Railway free tier (Dockerfile exists); Qdrant → Qdrant Cloud free 1GB (set `QDRANT_URL`/`QDRANT_API_KEY`); Supabase already cloud. Set all env vars including `WEB_ORIGIN` for CORS and confirm auth works cross-origin. Checkpointer note: on ephemeral free-tier disks SQLite checkpoints reset on redeploy — switch the checkpointer to Postgres (Supabase) now if feasible; otherwise record the limitation in `DECISIONS.md`.
2. **Seed the deployed instance:** run `seed_demo.py` against production so the demo isn't empty.
3. **Smoke-test on the real URLs:** the §5 harness pointed at the deployed API; plus a phone opening a real quiz link.
4. **Rewrite `demo_script.md`** as a tight 5-minute walkthrough on the deployed URLs: Faculty (login → curriculum upload → Lecture Flow → W-A-S with the gate shown deliberately → edit → download PPTX → quiz → answer it live on a phone → results appear) then Learner (detailed → resource card citations → diagrams → quiz nudge → progress rings). Every step must actually work; run it once end-to-end yourself.
5. **Final reconcile:** update `TODO.md` (real counts — they must change), `README.md` (deployed URLs, env table, one-command local run), `VERIFICATION.md` (final acceptance table), tag `v1.0`.

**Part E exit / FINAL ACCEPTANCE:**
1. Deployed URLs live; harness all-PASS against production.
2. Demo script executes cleanly, including the phone quiz.
3. RLS + throttling verified in production.
4. All Part C screens live and beautiful on the deployed app.
5. `TODO.md` counts changed and match the harness. If they still read 60/6, the sprint is not done.

---

## ORDER & CADENCE
**A → B → C → D → E.** A is non-negotiable first (proof + security). If time runs short before a deadline, cut in this order: D4 embedding cache → B3 drill-down tree (keep flat list) → C5 topic tree visuals → D6 checkpoint prune. Never cut A, the harness run, or the TODO reconcile.

After each part: run → prove → commit → one-paragraph summary → continue. If blocked, stop and report the exact blocker instead of marking done.

**Begin with A1 now: start the server and run `python prove_sprint2.py`.**
