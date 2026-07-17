# LearnForge — 5-Minute Demo Walkthrough

This script walks through every major feature of LearnForge, proving the robustness of the Layer 0 shared agent engine and the specialized platform front-doors.

## Prep
1. Ensure your `.env` contains `GEMINI_API_KEY`, `TAVILY_API_KEY`, and Supabase credentials.
2. Run `docker-compose up -d` in the root (for Qdrant & Langfuse).
3. Start the API (`uv run uvicorn main:app --reload` in `apps/api`).
4. Start the Web UI (`npm run dev` in `apps/web`).
5. Open http://localhost:3000

## Section 1: The Two Doors (0:00 - 0:30)
* **Action:** Land on the home page.
* **Talking point:** LearnForge isn't a generic chatbot. It's two independent platforms (Faculty and Learner) built on top of ONE shared LangGraph agent engine. The UI enforces a hard boundary, but the workflows are reusable.

## Section 2: Faculty Flagship — Lecture Flow & Script (0:30 - 2:00)
* **Action:** Click "I'm Faculty" and select the 10th-grade class.
* **Action:** Toggle the `[Lecture Script]` chip. Prompt: *"Prepare a lesson on the Cardiac Cycle."*
* **Observation:** Watch the streaming generation. Notice how the output isn't a chat bubble, but a beautifully rendered glass Artifact Card.
* **Talking point:** The agent detects the chip and routes to the `lecture_wf`. It generates a structured 3-part script (Intro, Body, Quiz) based on the teacher's configured class level and region.

## Section 3: Visuals & Assessment (2:00 - 3:30)
* **Action:** Toggle `[Diagrams]` and `[Quiz]`. Prompt: *"Visuals and a quiz for the Cardiac Cycle."*
* **Observation:** The Agent parallelizes or composes workflows.
  - The **Diagram Gallery** renders web-fetched images with an AI-generated "easy, simple, accurate" breakdown.
  - The **Quiz Link** renders as a shareable link.
* **Talking point:** The quiz is pushed to Supabase and generates a public URL. Students can answer on their phones, and results pipe right back into the DB.

## Section 4: Learner Self-Study & Resources (3:30 - 5:00)
* **Action:** Open a new incognito window and click "I'm a Learner".
* **Action:** Toggle `[Resource]` and `[Flashcards]`. Prompt: *"Help me study Transformer Architectures."*
* **Observation:** 
  - The **Resource Card** synthesizes live data from Tavily (news) and arXiv (papers) with inline citations.
  - The **Flashcards** render as interactive 3-D flip cards.
* **Talking point:** Everything the learner touches is logged to their session memory. When they click `[Quiz Me]`, the agent tests them on these specific topics, building a weakness profile that grounds future explanations.
