# Compass — AI Education Content Platform

Chat-first platform where teachers and students describe what they need, and a LangGraph agent generates quizzes, slides, notes, and diagrams with weak-spot memory, web grounding, and human-in-the-loop review.

## Stack

- **Frontend:** React (Vite) + TypeScript + Tailwind + Framer Motion
- **Backend:** FastAPI + Motor (MongoDB) + LangGraph
- **LLMs:** Groq (intent/quiz/notes/diagram) + Gemini (slides)
- **Scraping:** httpx + BeautifulSoup (Crawl4AI omitted on Windows due to litellm/Rust build; same grounding contract)

## Quick start

### 1. MongoDB

Ensure MongoDB is running locally (or set an Atlas URI):

```bash
# Local URI used by default
mongodb://localhost:27017/edtech
```

### 2. Backend

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env   # then fill GROQ_API_KEY / GEMINI_API_KEY
uvicorn app.main:app --reload --app-dir . --port 8000
```

From `backend/`:

```bash
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

### Optional Playwright (richer scrape pages)

```bash
backend\.venv\Scripts\playwright install chromium
```

## Auth notes

- JWT is kept **in memory only** on the frontend (not localStorage).
- Roles: `teacher` | `student` with route guards.
- Protected probe: `GET /auth/me` with `Authorization: Bearer <token>`.

## Key API routes

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/auth/signup` | Create account |
| POST | `/auth/login` | Login + JWT |
| GET | `/auth/me` | Current user |
| POST | `/agent/chat` | SSE agent stream |
| POST | `/agent/approve` | Approve generated content |
| POST | `/agent/edit` | Edit + persist |
| POST | `/agent/regenerate` | Regenerate one content type |
| POST | `/agent/submit-quiz-answer` | Update weak spots |
| GET | `/student/weak-spots` | Student weak spots |
| GET | `/teacher/class-weak-spots` | Class aggregate |

## Phases implemented

1. Auth + dashboards
2. LangGraph + SSE streaming
3. Quiz / slides / diagram / notes generators
4. Reference scraper + grounding
5. Weak-spot memory + re-explain strategies
6. Human review gate + floating action bar
7. Polish (shimmer loaders, errors, empty states, mobile FAB)

Without API keys, generators return structured **fallback** content so the UI/graph still works end-to-end.

## Reference

See `edtech-platform-cursor-implementation-guide.md` for the full phased build guide.
