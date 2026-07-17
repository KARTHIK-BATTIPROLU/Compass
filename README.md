# LearnForge

An open-source, dual-platform learning environment powered by a unified LangGraph agent engine.

## Documentation
- **Architecture & Source of Truth:** Read [CONTEXT.md](./CONTEXT.md)
- **Execution Plan:** Read [TODO.md](./TODO.md)
- **Demo Script:** Read [demo_script.md](./demo_script.md)

## Quick Start (Local Development)

### 1. Prerequisites
- Docker (for Qdrant & Langfuse)
- Node.js (for Next.js frontend)
- Python 3.11+ / `uv` (for FastAPI backend)
- Supabase account (or local Supabase instance)

### 2. Environment Variables
Create `.env` files in both `apps/web` and `apps/api`.
**apps/api/.env:**
```env
GEMINI_API_KEY=your_gemini_key
TAVILY_API_KEY=your_tavily_key
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_supabase_key
# Optional: QDRANT_URL, LANGFUSE_PUBLIC_KEY, etc.
```

### 3. Run Backend Services
```bash
# Start vector DB
docker-compose up -d

# Start API
cd apps/api
uv venv
uv pip install -r pyproject.toml # or install manually per TODO
uv run uvicorn main:app --reload
```

### 4. Run Frontend
```bash
cd apps/web
npm install
npm run dev
```
Navigate to `http://localhost:3000`.

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
