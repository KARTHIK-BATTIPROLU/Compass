# LearnForge — 5-Minute Demo Walkthrough

This script walks through every major feature of LearnForge, proving the robustness of the Layer 0 shared agent engine and the specialized platform front-doors.

## Prep
1. Ensure your `.env` contains `GEMINI_API_KEY`, `GROQ_API_KEY`, and Supabase credentials.
2. The API is deployed on Render and the Web UI is on Vercel. 
3. Open the production Vercel URL. (If testing locally, `docker-compose up -d` for Qdrant, `uv run uvicorn main:app` for API, `npm run dev` for Web, and open http://localhost:3000).

## Section 1: The Two Doors (0:00 - 0:30)
* **Action:** Land on the home page.
* **Talking point:** LearnForge isn't a generic chatbot. It's two independent platforms (Faculty and Learner) built on top of ONE shared LangGraph agent engine. The UI enforces a hard boundary, but the workflows are reusable. Notice the dual-pane interface — chat on the left, interactive artifacts on the right.

## Section 2: Faculty Flagship — Lecture Flow & W-A-S (0:30 - 2:00)
* **Action:** Click "I'm Faculty" and select the 10th-grade class.
* **Action:** Toggle the `[Lecture]` chip. Prompt: *"Prepare a lesson structure on the Cardiac Cycle."*
* **Observation:** The output appears as an Artifact Card on the right pane.
* **Talking point:** The agent detects the chip and routes to the `lecture_wf`. It generates a structured Lecture Flow based on the teacher's configured class level and region.
* **Action:** Toggle the `[W-A-S]` chip. Prompt: *"Generate slides and script."*
* **Observation:** Two artifacts appear: a Slides presentation and a 3-tier Script (Weak, Average, Strong).
* **Talking point:** The W-A-S workflow reads the Lecture Flow and automatically generates leveled teaching scripts (Weak for struggling students, Average for standard, Strong for advanced).

## Section 3: Visuals & Assessment (2:00 - 3:30)
* **Action:** Toggle `[Diagrams]` and `[Quiz]`. Prompt: *"Visuals and a quiz for the Cardiac Cycle."*
* **Observation:** The Agent parallelizes the workflows.
  - The **Diagram Gallery** renders web-fetched images with an AI-generated "easy, simple, accurate" breakdown.
  - The **Quiz Link** renders as a shareable link.
* **Talking point:** The quiz is pushed to Supabase using Row Level Security (RLS) and generates a public URL. Students can answer on their phones, and results pipe right back into the DB securely.

## Section 4: Learner Self-Study & Resources (3:30 - 5:00)
* **Action:** Open a new incognito window and click "I'm a Learner".
* **Action:** Toggle `[Research]` and `[Flashcards]`. Prompt: *"Help me study Transformer Architectures."*
* **Observation:** 
  - The **Research Brief** synthesizes live data from Tavily (news), arXiv (papers), and Semantic Scholar with inline citations.
  - The **Flashcards** render as interactive 3-D flip cards and offer an Anki .apkg download.
* **Talking point:** Everything the learner touches is logged to their session memory. The system builds a weakness profile and tracks topic edges, ensuring future explanations adapt to their precise knowledge gaps. Even if the primary LLM provider goes down, our multi-tier fallback ensures they never see an error.
