# CONTEXT.md — LearnForge
### Single-Agent, Multi-Workflow Personalized Learning Platform
> This file is the source of truth for the project. Every feature, architecture, data model, and design decision lives here. Read this before touching any code. Execution order lives in `TODO.md`.

---

## 0. One-Paragraph Summary

LearnForge is **two independent platforms sharing one agent engine**:

1. **Faculty Platform** — teachers select a class (9th / 10th / Undergrad), land in a ChatGPT-style chat with **floating feature icons**, and generate lecture flows, Weak-Average-Strong (W-A-S) scripts + presentations, quizzes, worksheets, diagrams, flashcards, and research updates — all curriculum-aware, region-aware, language-aware, downloadable, and editable in-session.
2. **Self-Learner Platform** — students (Undergrad / MBBS) get the same chat interface with their own floating icons: detailed step-by-step explanations, visual/flashcard generation, simple-and-accurate mode, a live resource feed (news + research papers + official docs), end-of-session quizzes, weak-topic tracking, and automatic session/topic organization backed by a **vector DB + graph DB memory**.

Underneath both sits **one LangGraph agent** that routes every request to the right workflow subgraph. Nothing is a separate "agent product" — features are **workflows stacked in layers**, activated by context.

---

## 1. The Two Platforms (Hard Boundary)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        LEARNFORGE MONOREPO                          │
│                                                                     │
│   ┌──────────────────────┐        ┌──────────────────────┐          │
│   │  FACULTY PLATFORM    │        │ SELF-LEARNER PLATFORM│          │
│   │  /faculty/*          │        │  /learn/*            │          │
│   │  (independent UI,    │        │  (independent UI,    │          │
│   │   independent auth   │        │   independent auth   │          │
│   │   role, own routes)  │        │   role, own routes)  │          │
│   └──────────┬───────────┘        └──────────┬───────────┘          │
│              │                               │                      │
│              └───────────┬───────────────────┘                      │
│                          ▼                                          │
│              ┌─────────────────────────┐                            │
│              │  SHARED AGENT ENGINE    │                            │
│              │  (LangGraph, FastAPI)   │                            │
│              │  one graph, many        │                            │
│              │  workflow subgraphs     │                            │
│              └─────────────────────────┘                            │
└─────────────────────────────────────────────────────────────────────┘
```

**Why a hard boundary at the UI, shared engine below:** the interviews showed teachers and self-learners must never feel like they're using "the other person's tool," but every workflow (explain, tier, quiz, visual, research, track) is identical machinery with different parameters. Build workflows once; give each platform its own front door.

---

## 2. Personas → Feature Mapping (traceability)

| Interview persona | Platform | Features that answer their pain |
|---|---|---|
| Aditi (school teacher) | Faculty | Class selection, Lecture Flow, W-A-S script + presentation, Quiz/Worksheets (PDF), Curriculum upload, Region+Language, Engaging Diagrams, Flashcards |
| Vikram (professor) | Faculty (Undergrad class) | Update & Research, Detailed, Quiz (shareable), Curriculum, Diagrams |
| Rahul (CS undergrad) | Self-Learner | Detailed Explanation, Simple & Accurate, Resource feed (docs/papers/news), Session quiz, Weakness tracking, Topic memory |
| Nisha (MBBS) | Self-Learner | Diagrams/Visuals + Flashcards, Detailed Explanation, Resource organization, Weakness tracking, Session history |
| Sanjay (tutor) | Faculty (small-batch mode, later) | Worksheets (PDF), Quiz shareable link, W-A-S tiers per student — deferred to post-MVP |

---

## 3. FACULTY PLATFORM — Feature Specifications

### 3.1 Onboarding & Registration
Collected **once at registration** (not per-chat):
- Name, email (Google OAuth)
- **Region** (state/board context, e.g., Telangana / CBSE / ICSE / University)
- **Language** (English / Hindi / Telugu … drives generation language)
- Subjects taught

These become part of the **agent's system context for every request** — the teacher never re-enters them.

### 3.2 Class Selection (entry gate)
After login, before chat:
```
┌───────────────────────────────┐
│   Which class are you         │
│   preparing for today?        │
│                               │
│   [ 9th ]  [ 10th ]  [ UG ]   │
└───────────────────────────────┘
```
- Selection sets `class_level` in session state.
- `class_level` changes: vocabulary depth, example complexity, curriculum lookup source, quiz difficulty band.
- Persisted per chat session; switchable from a dropdown in the chat header.

### 3.3 The Chat Interface (core surface)
ChatGPT-style conversation with **floating feature chips** above/around the input box. Chips are **toggles/modes**, not one-shot buttons — selecting one changes what the next prompt produces.

```
┌──────────────────────────────────────────────────────────────┐
│  LearnForge · Faculty          Class: 9th ▾   Lang: EN ▾     │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│   (conversation stream — glassmorphic message cards)         │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ ⌘ Floating chips (horizontally scrollable, glass pills):     │
│ [Lecture Flow] [W-A-S] [Quiz] [Worksheet] [Update&Research]  │
│ [Detailed] [Diagrams] [Flashcards] [Curriculum]              │
├──────────────────────────────────────────────────────────────┤
│  ✏️  "Prepare photosynthesis for tomorrow…"        [Send ➤]  │
└──────────────────────────────────────────────────────────────┘
```

### 3.4 Feature: **Lecture Flow**
**What:** Full session plan for ONE lecture — how it starts, hook/opening, topic order, transitions, examples per segment, activities, timing, how it closes, recap.
**Output:** A structured "Lecture Flow" document (editable in-session, downloadable as PDF/DOCX).
**Rule:** Lecture Flow is a **prerequisite flag for the Script** (see 3.5).

```
User prompt + [Lecture Flow] chip
        │
        ▼
┌─────────────────────┐
│ ROUTER (LangGraph)  │──► workflow: lecture_flow
└─────────────────────┘
        │
        ▼
┌──────────────────────────────────────────────┐
│ lecture_flow subgraph                        │
│  1. fetch curriculum context (if uploaded)   │
│  2. outline: open → segments → close         │
│  3. per-segment: objective, example, timing  │
│  4. format as Flow Doc (markdown → export)   │
└──────────────────────────────────────────────┘
        │
        ▼
  session_state.lecture_flow = doc   ← unlocks Script generation
```

### 3.5 Feature: **W-A-S (Weak / Average / Strong)** — the flagship
**What:** Generates TWO documents for the lecture:
1. **Presentation** (slide deck) — always created when W-A-S is selected.
2. **Script** — the teacher's full spoken/teaching flow — **created ONLY IF a Lecture Flow exists** in the session. No Lecture Flow → no Script (presentation only).

**The Script is sectioned in three tiers, in teaching order:**
```
┌────────────────────────────────────────────┐
│  SCRIPT: <topic>                           │
│  ────────────────────────────────────────  │
│  §1  WEAK section  (start here)            │
│      - grasp the absolute basics           │
│      - simplest analogies, local examples  │
│      - slow, confidence-building           │
│  ────────────────────────────────────────  │
│  §2  AVERAGE section                       │
│      - the full standard explanation       │
│      - push understanding of the whole     │
│  ────────────────────────────────────────  │
│  §3  STRONG section  (end here)            │
│      - advanced angles, extensions,        │
│        exam-level & beyond-syllabus hooks  │
└────────────────────────────────────────────┘
```
This mirrors real classroom flow: open by grounding the weakest students, carry the average through the whole concept, close by stretching the strongest.

**W-A-S workflow architecture:**
```
User + [W-A-S] chip
   │
   ▼
router ──► was_workflow
   │
   ├─► check: session_state.lecture_flow exists?
   │        │yes                     │no
   │        ▼                        ▼
   │   script_generator          (skip script)
   │   (3-tier, follows the
   │    Lecture Flow order)
   │
   └─► presentation_generator (always)
            │
            ▼
      slides.md → export engine → .pptx / reveal.js preview
   │
   ▼
Both artifacts land in the session's Artifact Panel:
editable in-session, downloadable (PDF / PPTX / DOCX)
```

### 3.6 Feature: **Quiz** (online, shareable)
- Generates an interactive quiz on the current topic, difficulty banded by `class_level`.
- **Shareable asset:** a public link (`/q/<token>`) the teacher can send to students directly (WhatsApp-friendly). Students answer without accounts; results stream back to the teacher's session.
- Result ingestion feeds the (post-MVP) class weak-spot tracker.

```
[Quiz] chip → quiz_workflow
   │  generate MCQ/short-answer set (JSON schema)
   ▼
store quiz → mint share token → /q/<token> page (no-auth answering)
   ▼
responses → results table → teacher dashboard card in chat
```

### 3.7 Feature: **Worksheet** (physical, PDF)
- Printable practice sheet: problems + space to work, answer key on last page.
- One click → **Download PDF**. Optionally tiered (W/A/S variants) if W-A-S mode is also active.

### 3.8 Feature: **Update & Research**
- Pulls from **official documentation + research papers** on the topic:
  - Official docs (language/framework/board official sites) via targeted search + fetch.
  - Papers via **arXiv API** and **Semantic Scholar API** (both free).
- Returns: what's new, what's relevant for upcoming teaching, links + 2-line relevance notes.
- Sources always cited at the end.

```
[Update & Research] → research_workflow
   │
   ├─► web search (Tavily free tier / self-hosted OpenSERP)
   ├─► arXiv API  (free, no key)
   ├─► Semantic Scholar API (free)
   ▼
rank by relevance to topic + class_level
   ▼
synthesized brief + cited source list
```

### 3.9 Feature: **Detailed**
- Step-by-step, beautifully structured deep explanation of every topic/subtopic in the prompt. Headings, worked examples, common misconceptions, mini-summaries.
- Works standalone or layered on any other mode (e.g., Detailed + W-A-S = detailed 3-tier script).

### 3.10 Feature: **Engaging Diagrams**
- **Web-sourced**: fetches the most-used/most-relevant diagrams for the topic from the open web.
- Pipeline: image search (Openverse API — free, openly-licensed; fallback Wikimedia Commons API; fallback DuckDuckGo image search self-hosted) → dedupe → relevance-rank via vision-capable LLM → present top N with source attribution.
- Only openly-licensed / attributable images preferred (Openverse first) — legally safe for classroom reuse.

### 3.11 Feature: **Flashcards**
- Generated (not scraped): front/back Q-A cards on the topic.
- Rendered as flip-cards in chat; **downloadable** (PDF print sheet + Anki-compatible CSV).

### 3.12 Feature: **Curriculum**
- Dedicated panel: teacher **uploads curriculum** (PDF/DOCX/image of syllabus).
- Parsed → chunked → embedded → stored in vector DB, tagged `{teacher_id, class_level, region}`.
- From then on, **every workflow retrieves curriculum context first** (RAG) so all outputs align to the actual syllabus. Region + language flow in from registration.

```
Upload syllabus.pdf
   │  parse (unstructured/pymupdf) → chunk → embed
   ▼
Vector DB (curriculum collection, metadata: teacher, class, region)
   ▼
Every generation workflow: retrieve top-k curriculum chunks → inject into prompt
```

### 3.13 In-session Editing & Downloads (cross-cutting)
- Every artifact (flow, script, slides, worksheet, flashcards) opens in an **Artifact Panel** beside chat: rich-text editable, regenerate-section button, then export.
- Export matrix: PDF (all), PPTX (presentation), DOCX (script/flow), CSV (flashcards), link (quiz).

---

## 4. SELF-LEARNER PLATFORM — Feature Specifications

### 4.1 Onboarding
- Login (Google OAuth) → short form: standard (**Undergrad / MBBS**), field/branch, exam context (e.g., NEET PG, placements) — optional, can also be gathered conversationally in the first chat.
- **Context-first rule:** before the first substantive answer in any session, the agent must hold: standard, subject context, and goal. If missing → ask ONE compact clarifying question. This context prefixes all generation.

### 4.2 Chat Interface (same skeleton, different chips)
```
Chips: [Detailed Explanation] [Diagrams] [Simple & Accurate]
       [Resource] [Quiz Me] [My Progress]
```

### 4.3 Feature: **Detailed Explanation**
- Step-by-step breakdown of the requested topic, structured beautifully (numbered steps, sub-headings, worked examples).
- **Mid-conversation drill-down:** any subtopic in the answer is clickable / mentionable — "explain step 3 in detail" spawns a focused sub-explanation, and that subtopic is registered in the topic graph (see 4.8).

### 4.4 Feature: **Diagrams (Visuals + Flashcards)**
- Same web-image pipeline as faculty (Openverse → Wikimedia → ranked), **plus** a generated breakdown: each returned image gets an "easy, simple, accurate" annotated explanation of what the image shows, part by part.
- Flashcards auto-generated alongside, downloadable (PDF/CSV).

### 4.5 Feature: **Simple & Accurate**
- Simplification mode: shortest correct explanation, calibrated to the learner's stated curriculum/exam context. No fluff, no loss of correctness. (Accuracy guard: generation is grounded on retrieved curriculum/official-source chunks when available; uncertain claims are flagged.)

### 4.6 Feature: **Resource** (industry-relevant feed)
On selection, fetch **three source classes** for the topic and show them grouped:
1. **News** (recent industry/medical news) — Tavily news search (free tier)
2. **Research papers** — arXiv + Semantic Scholar APIs
3. **Official documentation** — targeted fetch of canonical docs

Then: content generated **based on** these sources, with all resources cited at the end of the response.

```
[Resource] → resource_workflow
   ├─► news search
   ├─► papers (arXiv / SemanticScholar)
   ├─► official docs fetch
   ▼
grouped Resource Card (3 tabs) → synthesis grounded on them → citations footer
```

### 4.7 Feature: **End-of-Session Quiz + Weakness Tracking**
- When a session winds down (user signals, or inactivity/wrap-up), agent offers a short quiz covering the session's topics.
- Quiz results → **weak-topic extraction** → written to the learner's Weakness Profile.
- **My Progress** chip shows: topics studied per session, per-topic mastery, weak topics resurfacing suggestions.

```
session topics ──► quiz (5–8 Qs) ──► score per topic
                                       │
                                       ▼
                        WeaknessProfile (topic → mastery 0..1)
                                       │
                                       ▼
             next sessions: agent prioritizes weak topics in
             suggestions ("You struggled with X — revisit?")
```

### 4.8 Feature: **Resource Organization / Session & Topic Memory** (the backbone)
Every session is summarized, its topics extracted, embedded, and linked.

**Two-store memory design (this is the answer to "is vector+graph efficient?" — yes, with this split):**
- **Vector DB (Qdrant, free/self-hosted or free cloud tier / Chroma for dev)** — stores: session summaries, message chunks, curriculum chunks, explanation artifacts. Purpose: *semantic retrieval* ("what did I study about glycolysis?").
- **Graph layer** — stores: `(User)-[:STUDIED {date, session}]->(Topic)-[:SUBTOPIC_OF]->(Topic)`, `(Topic)-[:WEAK_FOR {score}]->(User)`. Purpose: *structural queries* ("what topics under Pathology have I touched, in which sessions, which are weak?").
- **Practical recommendation:** do **NOT** run Neo4j for MVP. Model the graph in **PostgreSQL** (tables: `topics`, `topic_edges`, `user_topic_events`) — this is a small, shallow graph; recursive CTEs handle it. Swap to Neo4j Aura (free tier) only if traversal complexity grows. One database fewer = one failure mode fewer at a hackathon.

```
End of every exchange:
  message → topic extractor (LLM, cheap model) → topics[]
     │                                              │
     ▼                                              ▼
  embed & upsert chunk (Qdrant)          upsert nodes/edges (Postgres graph)
     │                                              │
     └────────────► Session page: timeline of sessions,
                    topics per session, topic → sessions reverse view,
                    weak topics highlighted
```

---

## 5. THE SHARED AGENT ENGINE (LangGraph)

### 5.1 Master Graph
One graph, one entry, conditional routing to workflow subgraphs. Chips set `mode[]` in the request; the router combines mode + prompt intent.

```
                    ┌────────────────────┐
   request ───────► │  context_loader     │  (user profile, class_level,
   {prompt,         │  (region, language, │   curriculum RAG, weakness
    modes[],        │   session state)    │   profile)
    session_id}     └─────────┬──────────┘
                              ▼
                    ┌────────────────────┐
                    │      ROUTER        │  LLM-classified intent + explicit
                    └─────────┬──────────┘  mode chips (chips win on conflict)
      ┌───────────┬───────────┼───────────┬─────────────┬──────────┐
      ▼           ▼           ▼           ▼             ▼          ▼
 lecture_flow   was_wf     quiz_wf   worksheet_wf  research_wf  detailed_wf
      │           │           │           │             │          │
      ▼           ▼           ▼           ▼             ▼          ▼
      └───────────┴───────────┴─────┬─────┴─────────────┴──────────┘
                                    ▼
                          ┌────────────────────┐
                          │  diagrams_wf /      │  (composable — can run
                          │  flashcards_wf      │   after any workflow)
                          └─────────┬──────────┘
                                    ▼
                          ┌────────────────────┐
                          │  memory_writer      │  topic extraction →
                          │  (ALWAYS runs)      │  vector upsert + graph upsert
                          └─────────┬──────────┘
                                    ▼
                          ┌────────────────────┐
                          │  artifact_composer  │  stream to UI, register
                          │  + streamer         │  downloadables
                          └────────────────────┘
```

### 5.2 State Schema (LangGraph `State`)
```python
class AppState(TypedDict):
    user: UserProfile          # role, region, language, standard
    session_id: str
    class_level: str | None    # faculty only: "9th" | "10th" | "ug"
    modes: list[str]           # active chips
    prompt: str
    curriculum_ctx: list[Chunk]   # RAG retrieval
    weakness_ctx: WeaknessProfile | None
    lecture_flow: Doc | None      # gates script generation
    artifacts: list[Artifact]     # everything produced this turn
    topics_touched: list[str]     # for memory_writer
    citations: list[Source]
```

### 5.3 Workflow Composition Rules (features stack)
- Chips compose: `[Detailed]+[W-A-S]` → detailed 3-tier script. `[Quiz]+[Worksheet]` → both artifacts one turn.
- `memory_writer` runs on **every** turn (both platforms).
- `context_loader` runs on **every** turn — region/language/curriculum are never re-asked.
- Script generation is **gated** on `lecture_flow != None`.
- Every artifact is editable before export (human-review principle from interviews).

---

## 6. Tech Stack (chosen for free tiers + your LangGraph experience)

| Layer | Choice | Why / cost |
|---|---|---|
| Agent orchestration | **LangGraph (Python)** | You already build in it; best-in-class for stateful branching workflows, human-in-loop, durable state. |
| Backend API | **FastAPI** + SSE streaming | Async, streams intermediate workflow output to UI. |
| LLM | **Gemini free tier** (primary) + **Groq free tier** (fast/cheap topic-extraction & routing) | Zero cost for hackathon; two providers = fallback. |
| Embeddings | `BAAI/bge-small` local **or** Gemini embeddings free tier | Free either way. |
| Vector DB | **Qdrant** (free cloud 1GB / Docker self-host); Chroma for local dev | Free, LangChain-native. |
| Graph memory | **PostgreSQL** (Supabase free tier) — `topics`, `topic_edges`, `user_topic_events`; recursive CTEs | Avoids running Neo4j; upgrade path: Neo4j Aura free. |
| Relational data | Same **Supabase Postgres** (users, sessions, quizzes, artifacts) + Supabase Auth (Google) + Storage (uploads/exports) | One free service covers DB+auth+files. |
| Web search | **Tavily** (free 1k credits/mo) or self-hosted **OpenSERP** (free, Docker) | Research + news + docs discovery. |
| Image sourcing | **Openverse API** (free, openly-licensed) → **Wikimedia Commons API** (free) → DDG images fallback | Legally safe "most-used diagram" retrieval with attribution. |
| Papers | **arXiv API** + **Semantic Scholar API** | Free, no key (SemScholar key optional). |
| Doc parsing | PyMuPDF + `unstructured` | Curriculum upload parsing. |
| Exports | `python-docx`, `python-pptx`, `weasyprint` (PDF), `genanki`/CSV (flashcards) | All OSS. |
| Frontend | **Next.js 14 + Tailwind + shadcn/ui + Framer Motion** | Glassmorphism + animation quality with least effort. |
| Observability | **Langfuse self-hosted** (free) | Trace every LangGraph run; judges love visible reasoning. |
| Deploy | Vercel (FE) + Railway/Render free (BE) + Supabase + Qdrant cloud | All free-tier. |

**Inspiration references:** ChatGPT/Claude chat UX (chips ≈ tool toggles), Perplexity (cited resource feed), Anki (flashcards/spaced model), Khanmigo & NotebookLM (grounded educational generation), reveal.js (in-browser slide preview).

---

## 7. UI / Design System — Glassmorphism

- **Base:** dark gradient mesh background (deep indigo → violet), floating glass cards: `backdrop-blur-xl bg-white/10 border border-white/15 rounded-2xl shadow-lg`.
- **Chips:** pill-shaped glass toggles; active chip gets accent glow (`ring-2 ring-indigo-400/60`) + subtle scale spring (Framer Motion `whileTap`, `layout`).
- **Message stream:** user right / agent left, glass cards, streamed text with fade-in per token block.
- **Artifact Panel:** slides in from right (Framer Motion `AnimatePresence`), tabs per artifact, edit ↔ preview toggle, export bar bottom.
- **Micro-animations:** chip select ripple, quiz card flip (rotateY), flashcard 3D flip, progress rings on My Progress.
- **Accessibility:** all glass surfaces maintain ≥4.5:1 text contrast; reduced-motion media query respected.

---

## 8. Data Model (core tables)

```
users(id, role[faculty|learner], name, email, region, language, standard, created_at)
sessions(id, user_id, class_level, title, started_at, summary)
messages(id, session_id, role, content, modes[], created_at)
artifacts(id, session_id, type[flow|script|slides|worksheet|quiz|flashcards|resource_brief],
          content_md, export_urls jsonb, editable bool, created_at)
curricula(id, user_id, class_level, region, file_url, parsed bool)
quizzes(id, artifact_id, share_token, questions jsonb, open bool)
quiz_responses(id, quiz_id, respondent_name, answers jsonb, score, per_topic jsonb, created_at)
topics(id, name, subject, parent_id nullable)          -- graph nodes
topic_edges(parent_id, child_id, relation)             -- graph edges
user_topic_events(user_id, topic_id, session_id, kind[studied|quizzed|weak], score, at)
weakness_profiles(user_id, topic_id, mastery float, last_seen)
```

Vector collections (Qdrant): `curriculum_chunks`, `session_chunks`, `artifact_chunks` — all with `{user_id, session_id, topic}` payload metadata.

---

## 9. Non-Negotiable Principles (from user research)

1. **Nothing auto-publishes** — every artifact is editable before export/share.
2. **Context is loaded, never re-asked** — region, language, class, curriculum ride along automatically.
3. **Citations always** — research/resource outputs end with their sources.
4. **Chips compose** — features are layers, not silos.
5. **Memory always writes** — every turn updates topic graph + vectors; progress tracking is a side effect, never a chore.
6. **Script requires Flow** — enforced in state, not in prompt.
