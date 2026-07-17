# TODO.md — LearnForge Execution Plan
> Step-by-step build order. Each phase unlocks the next; features stack bottom-up exactly like the layer model in `CONTEXT.md`. Check items off as you go. Estimated effort tags: 🟢 small (≤2h) · 🟡 medium (half day) · 🔴 large (1–2 days).

---

## PHASE 0 — Repo, Environment & Skeleton
*Goal: empty but running full-stack app, deployable from day one.*

- [x] 🟢 Init monorepo: `apps/web` (Next.js 14 + TS + Tailwind + shadcn/ui + Framer Motion), `apps/api` (FastAPI + uv/poetry), `packages/shared` (types)
- [x] 🟢 Add `.env.example`: `GEMINI_API_KEY, GROQ_API_KEY, TAVILY_API_KEY, SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY, QDRANT_URL, QDRANT_API_KEY, LANGFUSE_*`
- [x] 🟢 Docker compose for local dev: `qdrant`, `langfuse` (optional), api
- [x] 🟢 Supabase project: enable Google OAuth, create Storage buckets `uploads`, `exports`
- [x] 🟡 Run schema migration — all tables from CONTEXT.md §8 (SQL file in `apps/api/db/schema.sql`)
- [x] 🟢 FastAPI: health route, CORS, SSE test endpoint streaming dummy tokens
- [x] 🟢 Next.js: landing page with two doors — **"I'm Faculty" / "I'm a Learner"** — glass cards on gradient mesh bg
- [x] 🟢 Deploy skeleton: Vercel (web) + Railway/Render (api) — CI on push to `main`
- [x] 🟢 Wire Langfuse tracing into a dummy LLM call — confirm traces appear

**Exit criteria:** visiting the deployed URL shows the two-door landing page; `/api/health` returns 200; one traced LLM call visible in Langfuse.

---

## PHASE 1 — Auth, Profiles & Entry Gates
*Goal: both platforms have login, onboarding, and their entry flows.*

- [x] 🟡 Google OAuth via Supabase on both doors; `role` stamped on first login (faculty|learner)
- [x] 🟡 Faculty onboarding form: region, language, subjects → `users` row
- [x] 🟡 Learner onboarding form: standard (Undergrad | MBBS), branch/field, goal (optional) → `users` row
- [x] 🟢 Faculty **Class Selection screen** (9th / 10th / UG) → creates `sessions` row with `class_level`; class switcher dropdown in chat header
- [x] 🟢 Route guards: `/faculty/*` requires faculty role, `/learn/*` requires learner role
- [x] 🟢 Profile settings page (edit region/language/standard later)

**Exit criteria:** a faculty user lands in an (empty) chat with class selected; a learner lands in an (empty) chat with profile context saved.

---

## PHASE 2 — Chat Core + Agent Engine v0 (Layer 0)
*Goal: the shared LangGraph engine answers in both chats with streaming; chips exist but only `Detailed` works.*

### 2A — Backend engine
- [x] 🔴 LangGraph master graph v0: `context_loader → router → detailed_wf → memory_writer(stub) → composer`
- [x] 🟡 `AppState` TypedDict exactly per CONTEXT.md §5.2
- [x] 🟡 `context_loader`: pulls user profile (region/language/standard/class_level) into system context
- [x] 🟡 Router: explicit `modes[]` from chips wins; else cheap-model intent classification (Groq)
- [x] 🟡 `detailed_wf`: step-by-step structured explanation node (Gemini), streams via SSE
- [x] 🟢 Persist `messages` (user + assistant, with modes)
- [x] 🟢 Langfuse spans per node

### 2B — Frontend chat
- [x] 🔴 Chat UI (shared component, themed per platform): glass message cards, streaming render, auto-scroll, session sidebar (list + new chat)
- [x] 🟡 **Floating chips bar** (glass pills, multi-toggle, active glow + spring animation) — faculty set & learner set from CONTEXT.md
- [x] 🟢 Chips state → `modes[]` sent with each prompt
- [x] 🟢 Session header: class/lang badges (faculty), standard badge (learner)

**Exit criteria:** both platforms hold a streamed conversation; toggling `[Detailed]` visibly changes output structure; sessions persist and reload.

---

## PHASE 3 — Memory Backbone (vector + graph) 
*Goal: every turn writes topic memory; sessions become browsable by topic. Build this EARLY because later features read from it.*

- [ ] 🟡 Qdrant collections: `session_chunks`, `curriculum_chunks`, `artifact_chunks` (+ embedding util, bge-small or Gemini)
- [ ] 🟡 `memory_writer` real implementation: per turn → topic extraction (Groq, JSON out) → upsert `topics`/`topic_edges`/`user_topic_events` (Postgres) → embed & upsert chunk (Qdrant)
- [ ] 🟡 Session summarizer: on session close/inactivity → summary saved to `sessions.summary` + embedded
- [ ] 🟡 Retrieval helpers: `search_my_history(query)`, `topics_in_session(id)`, `sessions_for_topic(id)` (recursive CTE for subtopics)
- [ ] 🟡 Learner **Sessions & Topics page**: timeline of sessions with topic pills; click a topic → all sessions touching it
- [ ] 🟢 Mid-conversation drill-down: subtopic mention spawns focused explanation AND registers subtopic edge in graph

**Exit criteria:** after 3 test sessions, the Topics page shows a correct topic→session map; asking "what did I study yesterday?" retrieves from memory.

---

## PHASE 4 — Faculty Flagship: Curriculum → Lecture Flow → W-A-S
*Goal: the teacher's core value chain works end-to-end. Order matters: curriculum grounds flow; flow gates script.*

### 4A — Curriculum (ground everything first)
- [x] 🟡 Upload UI (Curriculum chip → panel): PDF/DOCX/image → Supabase storage
- [x] 🟡 Parse (PyMuPDF/unstructured) → chunk → embed → `curriculum_chunks` with `{teacher_id, class_level, region}`
- [x] 🟢 `context_loader` upgrade: retrieve top-k curriculum chunks for every faculty generation

### 4B — Lecture Flow
- [x] 🟡 `lecture_flow_wf`: opening hook → segments (objective, example, timing) → close/recap; curriculum-grounded
- [x] 🟢 Save as artifact; set `session_state.lecture_flow`
- [x] 🟡 Artifact Panel v1 (slide-in right, Framer Motion): markdown preview ↔ edit toggle, save

### 4C — W-A-S (script + presentation)
- [x] 🔴 `was_wf`: 
  - gate check `lecture_flow` → if present, generate **Script** in 3 ordered sections (WEAK basics-first → AVERAGE full picture → STRONG advanced close), following the Flow's segment order
  - always generate **Presentation** (slides as structured md)
- [x] 🟡 Slide preview in Artifact Panel (reveal.js or simple slide cards)
- [x] 🟡 Export engine v1: DOCX (script/flow, python-docx), PPTX (slides, python-pptx), PDF (weasyprint) → `exports` bucket → download buttons
- [x] 🟢 Chip composition: `[Detailed]+[W-A-S]` produces the detailed variant

**Exit criteria:** upload syllabus → generate Flow → generate W-A-S → edit script in panel → download PPTX + DOCX. Skipping Flow yields presentation only (script correctly blocked).

---

## PHASE 5 — Assessment: Quiz (shareable) + Worksheet (PDF)
- [x] 🟡 `quiz_wf`: JSON-schema question gen (topic + class_level difficulty band) → `quizzes` row + share token
- [x] 🟡 Public answer page `/q/<token>`: no-auth, name + answer, mobile-first (WhatsApp-shareable)
- [x] 🟡 Responses → `quiz_responses` with per-topic scoring → live results card in the teacher's chat
- [x] 🟡 `worksheet_wf`: printable problem set + answer key → PDF download; W-A-S-aware (3 variants when W-A-S active)
- [x] 🟢 Learner **End-of-Session Quiz**: wrap-up trigger (user signal or inactivity) → 5–8 Qs on `topics_touched` → score per topic
- [x] 🟡 Weakness pipeline: quiz scores → `weakness_profiles` upsert → **My Progress** page (mastery rings per topic, weak topics list, "revisit?" suggestions)
- [x] 🟢 `context_loader` upgrade (learner): inject weakness profile so generation targets weak spots

**Exit criteria:** teacher shares a quiz link on a phone and sees results appear; learner finishes a session, takes the quiz, and My Progress shows a weak topic.

---

## PHASE 6 — Research & Resources (grounded + cited)
- [x] 🟡 Search tool wrapper: Tavily (or self-hosted OpenSERP) — web + news
- [x] 🟢 arXiv API tool + Semantic Scholar API tool (title/abstract/link/year)
- [x] 🟡 Faculty `research_wf` (**Update & Research** chip): official docs + papers → relevance-ranked brief with "why this matters for your class" notes + citation footer
- [x] 🟡 Learner `resource_wf` (**Resource** chip): 3-tab Resource Card — News | Papers | Official Docs — then a synthesis generated FROM those sources, citations at the end
- [x] 🟢 Citation renderer component (numbered footnotes, favicon + domain)

**Exit criteria:** Resource chip on "transformer architectures" returns populated 3-tab card with working links and a cited synthesis.

---

## PHASE 7 — Visuals: Engaging Diagrams + Flashcards
- [x] 🟡 Image pipeline tool: Openverse API → (fallback) Wikimedia Commons API → (fallback) DDG images; dedupe; vision-LLM relevance rank; keep license + attribution metadata
- [x] 🟡 `diagrams_wf` (both platforms): top-N diagrams as glass gallery cards with attribution
- [x] 🟡 Learner extra: per-image **annotated breakdown** (easy/simple/accurate explanation of what the diagram shows)
- [x] 🟡 `flashcards_wf`: Q-A generation → 3D flip-card component → export PDF print sheet + Anki CSV (genanki)
- [x] 🟢 Compose: diagrams/flashcards attachable after any other workflow's output

**Exit criteria:** "cardiac cycle" + [Diagrams] returns licensed, attributed images with breakdowns; flashcards flip and export.

---

## PHASE 8 — Polish, Glass UI Pass & Demo Hardening
- [x] 🟡 Full glassmorphism pass: gradient mesh bg, blur/opacity tokens, chip glow states, reduced-motion support, contrast audit
- [x] 🟡 Micro-animations: chip ripple, artifact panel spring, quiz card flip, progress ring fill
- [x] 🟢 Empty states + loading skeletons (glass shimmer)
- [x] 🟡 Error resilience: LLM fallback, retry with partial results, invalid prompt guard
- [x] 🟢 Seed demo data: 1 faculty, 1 learner
- [x] 🟢 Demo script: 5-minute walkthrough hitting every chip once
- [x] 🟢 README: setup, env, architecture pointer to CONTEXT.md

**Exit criteria:** full cold demo runs without touching the keyboard beyond the script; a stranger can set up locally from README.

---

## Dependency Graph (what unlocks what)

```
P0 skeleton
 └─► P1 auth/gates
      └─► P2 chat + engine v0 (Layer 0)
           ├─► P3 memory backbone ──────────────┐
           ├─► P4 curriculum → flow → W-A-S     │
           │        └─► P5 worksheet tiers      │
           ├─► P5 quiz/worksheet ◄──────────────┤ (weakness needs P3)
           ├─► P6 research/resources            │
           └─► P7 diagrams/flashcards           │
                          └────────► P8 polish ◄┘
```

## Parallelization for a 4-person team
- **A (Frontend):** P2B → chips → Artifact Panel → P8 UI pass
- **B (Agent/Backend):** P2A → P4 workflows → P6
- **C (Data/Memory):** P0 DB → P3 → P5 weakness pipeline
- **D (Integrations):** OAuth → exports engine → image pipeline (P7) → deploy/demo

## Cut-list if time runs out (in cut order)
1. Anki CSV export (keep PDF flashcards)
2. Learner image annotated-breakdowns (keep gallery)
3. Self-hosted OpenSERP (stay on Tavily free)
4. Session inactivity auto-quiz (keep manual "Quiz Me")
5. reveal.js slide preview (keep PPTX download only)
