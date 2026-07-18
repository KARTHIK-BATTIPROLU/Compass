from agent.state import AppState
from agent.llm import get_fast_llm
from agent.prompt_utils import trim_history, summary_preamble
from langchain_core.messages import SystemMessage
from langfuse import observe
import os
import uuid
import json
import logging

logger = logging.getLogger(__name__)

_supabase = None
def get_supabase():
    global _supabase
    if _supabase is None:
        from supabase import create_client
        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_SERVICE_KEY", os.getenv("SUPABASE_ANON_KEY", ""))
        if url and key:
            _supabase = create_client(url, key)
    return _supabase

@observe()
async def quiz_wf_node(state: AppState):
    # Fast/cheap tier (Groq-primary): quiz output is plain JSON, not the
    # custom <artifact> tag format Groq is unreliable at (see get_fast_llm).
    llm = get_fast_llm(temperature=0.2)
    user = state.get("user", {})
    role = user.get("role", "learner")
    class_level = state.get("class_level", user.get("standard", "General"))
    
    curriculum_ctx = state.get("curriculum_ctx", [])
    ctx_str = "\n".join([c['content'] for c in curriculum_ctx])
    
    system_prompt = f"""You are LearnForge, generating a quiz.
Role: {role}, Level: {class_level}
Generate a 5-question multiple choice quiz based on the prompt and curriculum.
Your response MUST be ONLY a valid JSON object with this schema:
{{
  "title": "Quiz Title",
  "questions": [
    {{
      "id": "q1",
      "topic": "topic_name_for_tracking",
      "text": "Question text?",
      "options": ["A", "B", "C", "D"],
      "correctAnswer": 0,
      "explanation": "Why this is correct."
    }}
  ]
}}

CURRICULUM:
{ctx_str if ctx_str else "N/A"}
{summary_preamble(state.get("session_summary"))}"""

    messages = [SystemMessage(content=system_prompt)] + trim_history(state.get("messages", []))
    response = await llm.ainvoke(messages)
    
    quiz_data = {}
    try:
        raw = response.text
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0]
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0]
        quiz_data = json.loads(raw.strip())
    except Exception as e:
        print("Failed to parse quiz JSON:", e)
        quiz_data = {"title": "Error generating quiz", "questions": []}

    artifacts = state.get("artifacts", [])
    art_id = str(uuid.uuid4())
    session_id = state.get("session_id")

    if role == "faculty":
        token = str(uuid.uuid4())
        artifact_content = f'<artifact type="quiz_link" token="{token}">{json.dumps(quiz_data)}</artifact>'
        try:
            sb = get_supabase()
            if sb:
                # quizzes.artifact_id is a real FK to artifacts.id. composer_node
                # persists artifacts too, but only after this node returns, so we
                # create the row here first or the insert below violates the FK.
                sb.table("artifacts").upsert({
                    "id": art_id,
                    "session_id": session_id,
                    "type": "quiz",
                    "content_md": artifact_content,
                }, on_conflict="id").execute()
                sb.table("quizzes").insert({
                    "artifact_id": art_id,
                    "share_token": token,
                    "questions": quiz_data,
                    "open": True
                }).execute()
        except Exception as e:
            print("Failed to save quiz:", e)
    else:
        artifact_content = f'<artifact type="learner_quiz">{json.dumps(quiz_data)}</artifact>'

    artifacts.append({
        "id": art_id,
        "type": "quiz",
        "content": artifact_content,
        "created_at": "now"
    })
    
    response.content = artifact_content
    
    return {
        "messages": [response],
        "artifacts": artifacts
    }
