# AUDIT.md — LearnForge Ground-Truth Audit
> Generated: 2026-07-18. Every checkbox in TODO.md was cross-checked against actual file content. "Done" means the code exists AND is correctly wired. "Stub" means a file exists but does not implement the claimed behavior. "Missing" means no file/code exists at all.

---

## Summary

| Category | Claimed Done | Actually Done | Stubs | Missing |
|---|---|---|---|---|
| Phase 0 — Skeleton | 8 | 6 | 0 | 2 |
| Phase 1 — Auth | 6 | 3 | 3 | 0 |
| Phase 2 — Chat Engine | 9 | 5 | 4 | 0 |
| Phase 3 — Memory | 0 | 0 | 1 | 5 |
| Phase 4 — Curriculum/Flow/WAS | 7 | 1 | 5 | 1 |
| Phase 5 — Quiz/Worksheet | 6 | 1 | 4 | 1 |
| Phase 6 — Research/Resources | 5 | 2 | 3 | 0 |
| Phase 7 — Visuals | 4 | 1 | 3 | 0 |
| Phase 8 — Polish | 7 | 2 | 5 | 0 |
| **TOTAL** | **52** | **21** | **28** | **9** |

**Approximately 40% of "done" checkboxes are false. ~53% are stubs (file exists, behavior absent).**

---

## Detailed Findings

### PHASE 0

| Claim | Reality | Evidence |
|---|---|---|
| Init monorepo (Next.js 14 + FastAPI) | ✅ DONE | `apps/web`, `apps/api` directories exist with correct stacks |
| .env.example | ❌ MISSING | `.env.example` does not exist in repo root; only `apps/api/.env` |
| Docker compose | ✅ DONE | `docker-compose.yml` exists with qdrant + api |
| Supabase: Google OAuth + storage buckets | ⚠️ PARTIAL | Supabase configured; buckets not verified; Google OAuth broken (tested live) |
| Schema migration | ✅ DONE | `apps/api/db/schema.sql` exists with all tables |
| FastAPI health route + CORS + SSE test | ✅ DONE | `main.py` has `/api/health`, `/api/test/stream` |
| Next.js landing page (two doors) | ✅ DONE | `apps/web/src/app/page.tsx` exists |
| Deploy skeleton to Vercel + Railway | ❌ MISSING | No CI config, no Railway/Vercel config found |
| Langfuse tracing wired | ⚠️ PARTIAL | `@observe()` decorators present but no key configured; will silently fail |

### PHASE 1

| Claim | Reality | Evidence |
|---|---|---|
| Google OAuth (both platforms) | ⚠️ STUB | Code exists; tested live and returns "Unsupported provider" — not enabled in Supabase |
| Faculty onboarding form | ⚠️ STUB | `apps/web/src/app/onboarding/faculty/page.tsx` exists; not verified if it saves to `users` table |
| Learner onboarding form | ⚠️ STUB | `apps/web/src/app/onboarding/learner/page.tsx` exists; same concern |
| Faculty class selection screen | ⚠️ STUB | Referenced in faculty page; no evidence of `sessions` row creation |
| Route guards | ✅ DONE | `src/middleware.ts` exists with route protection |
| Profile settings page | ✅ DONE | `apps/web/src/app/faculty/settings` + `learn/settings` exist |

### PHASE 2

| Claim | Reality | Evidence |
|---|---|---|
| LangGraph master graph | ⚠️ STUB | `graph.py` exists but compiled with **no checkpointer** — all state dies every turn |
| AppState TypedDict | ✅ DONE | `state.py` matches spec |
| context_loader | ⚠️ CRITICAL BUG | Instantiates `QdrantClient` at module import time (line 15); crashes entire app if Qdrant is down |
| Router with chip modes | ⚠️ STUB | Router exists but: (a) missing W-A-S/was route, (b) phantom gate_wf logic for learners, (c) "Lecture Script" label doesn't match UI chip "Lecture Flow" |
| detailed_wf | ✅ DONE | File exists, calls Gemini |
| Persist messages | ⚠️ STUB | memory_writer saves raw messages only; no topic extraction; inserts both user+assistant every turn even if AI didn't respond yet |
| Langfuse spans | ⚠️ PARTIAL | `@observe()` on all nodes but no Langfuse keys configured |
| Chat UI (streaming, sidebar) | ✅ DONE | `ChatUI.tsx`, `Sidebar.tsx` exist |
| Floating chips bar | ⚠️ STUB | `FloatingChips.tsx` exists as reusable component; chip list definitions not verified against spec |

### PHASE 3 — MEMORY BACKBONE

| Claim | Reality | Evidence |
|---|---|---|
| Qdrant collections setup | ❌ NOT STARTED | No collection creation script; context_loader hard-codes "curriculum" collection |
| memory_writer real implementation | ❌ NOT STARTED | `memory_writer.py` only saves raw messages; no topic extraction, no Qdrant write |
| Session summarizer | ❌ NOT STARTED | No code exists |
| Retrieval helpers | ❌ NOT STARTED | No code exists |
| Sessions & Topics page | ❌ NOT STARTED | No page exists at `/learn/topics` or similar |
| Mid-conversation subtopic drill-down | ❌ NOT STARTED | No code exists |

### PHASE 4 — CURRICULUM / LECTURE FLOW / W-A-S

| Claim | Reality | Evidence |
|---|---|---|
| Upload UI (Curriculum chip → panel) | ❌ MISSING | `curriculum_wf.py` exists but no file upload endpoint; no upload UI component found |
| Parse → chunk → embed → Qdrant | ❌ MISSING | No parsing code; `ingest_dummy.py` exists as script but main upload path absent |
| context_loader curriculum retrieval | ⚠️ PARTIAL | Only retrieves when "Curriculum" in modes — should run for ALL faculty generations |
| lecture_flow_wf (hook/segments/close) | ❌ WRONG | `lecture_wf.py` outputs "Introduction / Body / Quiz" — NOT the spec shape. `lecture_flow` set to `{"active_lesson": True}` not a structured dict |
| Save as artifact; set session_state.lecture_flow | ⚠️ STUB | Sets a dict but structure is wrong and not persisted across turns (no checkpointer) |
| W-A-S `was_wf` | ❌ NOT STARTED | No `was_wf.py` file exists; `gate_wf.py` is a completely different (wrong) feature |
| Slide preview in Artifact Panel | ❌ NOT STARTED | ArtifactRenderer exists but no slide-specific rendering |
| Export engine (DOCX/PPTX/PDF) | ❌ NOT STARTED | No export endpoint; `python-docx`, `python-pptx`, `weasyprint` not in `pyproject.toml` |
| Chip composition [Detailed]+[W-A-S] | ❌ NOT STARTED | Router has no composition logic |

### PHASE 5 — ASSESSMENT

| Claim | Reality | Evidence |
|---|---|---|
| quiz_wf | ⚠️ STUB | `quiz_wf.py` exists; `quiz.py` router exists; not verified end-to-end |
| Public answer page /q/<token> | ✅ DONE | `apps/web/src/app/q/[token]/page.tsx` exists |
| Responses → live results card | ❌ NOT STARTED | No live results component in ChatUI or ArtifactRenderer |
| worksheet_wf | ⚠️ STUB | File exists; PDF export absent (weasyprint missing from deps) |
| Learner end-of-session quiz | ❌ NOT STARTED | No trigger mechanism exists |
| Weakness pipeline + My Progress page | ❌ NOT STARTED | No weakness calculation; no `/learn/progress` page |
| context_loader weakness injection | ⚠️ PARTIAL | Loads weakness_profiles from Supabase but `weakness_ctx` not injected into system prompts |

### PHASE 6 — RESEARCH / RESOURCES

| Claim | Reality | Evidence |
|---|---|---|
| Tavily wrapper | ✅ DONE | `search.py` has graceful fallback when key missing |
| arXiv + Semantic Scholar | ⚠️ PARTIAL | arXiv exists; **Semantic Scholar is absent** |
| research_wf | ⚠️ STUB | `research_wf.py` exists; not verified against spec (Update & Research chip) |
| resource_wf (3-tab card) | ⚠️ STUB | `resource_wf.py` exists; 3-tab UI component not found in ArtifactRenderer |
| Citation renderer | ⚠️ STUB | ArtifactRenderer has some citation parsing; not full numbered footnotes with favicons |

### PHASE 7 — VISUALS

| Claim | Reality | Evidence |
|---|---|---|
| Image pipeline (Openverse → Wikimedia → DDG) | ❌ STUB | `images.py` only uses DDG; Openverse/Wikimedia absent |
| diagrams_wf | ⚠️ STUB | `diagrams_wf.py` exists; calls images.py (DDG only) |
| Annotated breakdown per image | ❌ NOT STARTED | No vision-LLM annotation code |
| flashcards_wf + 3D flip component | ⚠️ STUB | `flashcards_wf.py` exists; Anki CSV/genanki absent from deps |

### PHASE 8 — POLISH

| Claim | Reality | Evidence |
|---|---|---|
| Full glassmorphism pass | ⚠️ PARTIAL | Chat UI has glass cards; not audited for contrast/reduced-motion |
| Micro-animations | ⚠️ PARTIAL | Framer Motion used for some elements |
| Empty states + loading skeletons | ⚠️ PARTIAL | Basic loading exists |
| Error resilience | ❌ MISSING | `chat_stream` catches exception and leaks `str(e)` to client (security bug) |
| Seed demo data | ⚠️ PARTIAL | `seed_demo.py` exists but depends on missing tables |
| Demo script | ✅ DONE | `demo_script.md` exists |
| README | ⚠️ WRONG | README still contains old MongoDB/Vite content |

---

## Critical Boot-Blockers (must fix before anything else)

1. **`context_loader.py` line 15**: `QdrantClient(url="http://localhost:6333")` at module import time → entire app crashes on startup if Qdrant is not running.
2. **`pyproject.toml`**: Missing `langchain-community`, `tavily-python`, `duckduckgo-search`, `arxiv`, `python-docx`, `python-pptx`, `weasyprint`, `pymupdf`, `python-multipart`, `python-jose[cryptography]`. App cannot import `search.py` or `images.py` without these.
3. **No checkpointer**: `graph.compile()` with no checkpointer → all state (lecture_flow, topics_touched, etc.) lost every turn. Multi-turn features are fundamentally broken.
4. **Router mismatch**: `router.py` checks for "Lecture Script" but UI chip is "Lecture Flow"; W-A-S chip not routable at all.
5. **CORS wildcard + credentials=True**: Invalid/unsafe combination per security spec.

---

## Security Findings

1. **Zero auth on all endpoints** — `/api/chat/stream`, `/api/messages/*`, quiz routes all unauthenticated.
2. **Stack traces leaked to client** — `chat_stream` yields `str(e)` directly.
3. **CORS**: `allow_origins=["*"]` + `allow_credentials=True` is invalid per browser security model.
4. **Service role key used everywhere** — bypasses RLS.
5. **No RLS on any table** — any user can read any session.
