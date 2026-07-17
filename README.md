# LearnForge (Compass)

An open-source, AI-native platform bridging the gap between educators and learners using agentic RAG and structured generative UI.

## Architecture

LearnForge is a monorepo containing:
- **`apps/web`**: Next.js 14 frontend (React, Tailwind, Framer Motion)
- **`apps/api`**: FastAPI backend powering the LangGraph agent engine
- **`packages/shared`**: Shared configurations (if any)

### The Agent Engine
LearnForge is powered by a **stateful LangGraph agent** (`apps/api/agent`). It features a single router that dispatches to multiple workflow nodes based on user intent (the "chips").
- **Faculty features**: Lecture Flow generation, W-A-S (Weak/Average/Strong) teaching scripts, Curriculum ingestion (PDF/DOCX RAG).
- **Learner features**: Socratic quizzes, Resource Cards (Semantic Scholar + Tavily), dynamic flashcard generation (.apkg), and spaced repetition (Weakness Profile).

### The Memory Backbone
Every session persists to a local SQLite checkpointer (`apps/api/data/checkpoints.db`).
At the end of every turn, the `memory_writer` node extracts topics, upserts them to Postgres (Supabase), and embeds the conversation turn into Qdrant (`session_chunks`). This allows long-term semantic recall and weakness profiling across sessions.

## Setup

### Prerequisites
- Python 3.12+ and `uv`
- Node.js 18+ and `npm`
- Docker (for Qdrant vector database)
- A Supabase project (for Postgres Auth + DB)
- API Keys: Google Gemini (`GEMINI_API_KEY`), Tavily (`TAVILY_API_KEY`)

### 1. Backend (FastAPI + LangGraph)
```bash
cd apps/api
cp .env.example .env # (Configure your keys, Supabase URL, etc.)
uv sync
docker-compose up -d # Starts Qdrant on port 6333
uv run uvicorn main:app --port 8000 --reload
```

### 2. Frontend (Next.js)
```bash
cd apps/web
npm install
# Configure .env.local with NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY
npm run dev
```

## Security & Auth
Supabase provides Goole OAuth and email authentication. The FastAPI backend verifies JWTs via PyJWT/Supabase Admin client. Ensure your Supabase RLS policies are active in production.
