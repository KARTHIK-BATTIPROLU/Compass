# AI Education Content Platform — Cursor AI Implementation Guide

This is a phased, iterative build plan. Keep this file open in Cursor as a reference
(`@edtech-platform-cursor-implementation-guide.md`) while working on individual slices.

## Project context

Chat-first interface where teachers and students describe what they need and a LangGraph
wrapper agent generates the right content type (slides, quizzes, notes, diagrams) with:

1. Prompt-to-content generation
2. Weak-spot memory
3. Re-explain on failure
4. Human-in-the-loop review
5. Curriculum/reference-grounded output

**Stack:** React/Vite/TS/Tailwind · FastAPI · LangGraph · Groq · Gemini · MongoDB · JWT · SSE via fetch()

**Design:** dark glassmorphism, spring Framer Motion, adaptive floating glass actions.

## Repo layout

See workspace `backend/` and `frontend/` (Compass root). Full target tree is in the product plan.

## Phases (sequential)

1. Scaffolding & Auth — signup/login, JWT, role dashboards
2. LangGraph skeleton + SSE stubs
3. Real content generators (quiz/slides/diagram/notes)
4. Scraper node + grounding
5. Weak-spot memory + re-explain
6. Human review gate + FloatingActionBar
7. Polish pass

## Environment

```
GROQ_API_KEY=
GEMINI_API_KEY=
MONGODB_URI=mongodb://localhost:27017/edtech
JWT_SECRET=
JWT_ALGORITHM=HS256
JWT_EXPIRY_MINUTES=1440
```

## Debugging loop

1. Exact error/stack trace
2. Isolate backend vs frontend
3. Targeted log at failure point
4. Fix only the isolated cause
5. Re-run Definition of Done for the current phase

Do not wrap failures in silent broad try/except.
