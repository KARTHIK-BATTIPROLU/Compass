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
