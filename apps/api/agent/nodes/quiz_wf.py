from agent.state import AppState
from agent.llm import get_fast_llm
from agent.prompt_utils import trim_history, summary_preamble
from agent.artifact_parser import extract_json_payload, generate_fallback_notice
from langchain_core.messages import SystemMessage
from langfuse import observe
import os
import uuid
import json
import logging

logger = logging.getLogger(__name__)

def get_supabase(jwt: str = None):
    from supabase import create_client, ClientOptions
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_ANON_KEY", "")
    
    if not url or not key:
        return None
        
    options = None
    if jwt:
        options = ClientOptions(headers={"Authorization": f"Bearer {jwt}"})
        
    return create_client(url, key, options=options)


@observe()
async def quiz_wf_node(state: AppState):
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
    
    quiz_data = extract_json_payload(response.text)
    artifacts = state.get("artifacts", [])
    
    if not quiz_data:
        logger.warning(f"[quiz_wf] Failed to extract JSON. Degrading.")
        response.content = response.text + generate_fallback_notice()
        return {
            "messages": [response],
            "artifacts": artifacts
        }

    art_id = str(uuid.uuid4())
    session_id = state.get("session_id")

    if role == "faculty":
        token = str(uuid.uuid4())
        artifact_content = f'<artifact type="quiz_link" token="{token}">\n{json.dumps(quiz_data)}\n</artifact>'
        try:
            sb = get_supabase(jwt=state.get("jwt"))
            if sb:
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
            logger.warning(f"Failed to save quiz: {e}")
    else:
        artifact_content = f'<artifact type="learner_quiz">\n{json.dumps(quiz_data)}\n</artifact>'

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
