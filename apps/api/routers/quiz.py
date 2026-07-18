from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client
import os
from typing import Dict, Any

router = APIRouter()
supabase: Client = create_client(
    os.getenv("SUPABASE_URL", "http://localhost:8000"),
    os.getenv("SUPABASE_SERVICE_KEY", os.getenv("SUPABASE_ANON_KEY", ""))
)

class QuizResponse(BaseModel):
    quiz_id: str
    respondent_name: str
    answers: Dict[str, Any]
    score: int
    per_topic: Dict[str, Any]

@router.get("/api/quiz/{token}")
async def get_quiz(token: str):
    res = supabase.table("quizzes").select("*").eq("share_token", token).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return res.data[0]

@router.post("/api/quiz/{token}/submit")
async def submit_quiz(token: str, req: QuizResponse):
    res = supabase.table("quizzes").select("id, artifacts(session_id)").eq("share_token", token).execute()
    if not res.data:
        raise HTTPException(status_code=404)
        
    db_quiz_id = res.data[0]["id"]
    session_id = res.data[0].get("artifacts", {}).get("session_id")
    
    supabase.table("quiz_responses").insert({
        "quiz_id": db_quiz_id,
        "respondent_name": req.respondent_name,
        "answers": req.answers,
        "score": req.score,
        "per_topic": req.per_topic
    }).execute()
    
    # ── Update weakness tracker ──────────────────────────────────────────────
    if session_id:
        sess_res = supabase.table("sessions").select("user_id").eq("id", session_id).execute()
        if sess_res.data:
            user_id = sess_res.data[0].get("user_id")
            if user_id and req.per_topic:
                for topic_name, score in req.per_topic.items():
                    # Find or create topic
                    topic_res = supabase.table("topics").select("id").eq("name", topic_name).execute()
                    if topic_res.data:
                        topic_id = topic_res.data[0]["id"]
                    else:
                        new_topic = supabase.table("topics").insert({"name": topic_name}).execute()
                        topic_id = new_topic.data[0]["id"]
                    
                    # Log event
                    try:
                        raw_score = float(score)
                        mastery = raw_score / 100.0 if raw_score > 1.0 else raw_score
                        mastery = max(0.0, min(1.0, mastery))
                        
                        supabase.table("user_topic_events").insert({
                            "user_id": user_id,
                            "topic_id": topic_id,
                            "session_id": session_id,
                            "kind": "quizzed",
                            "score": raw_score
                        }).execute()
                        
                        # Upsert weakness profile
                        supabase.table("weakness_profiles").upsert({
                            "user_id": user_id,
                            "topic_id": topic_id,
                            "mastery": mastery
                        }, on_conflict="user_id,topic_id").execute()
                    except Exception as e:
                        print(f"Failed to update weakness profile for {topic_name}: {e}")
    
    return {"status": "success"}
    
from agent.auth import get_current_user, user_owns_session
from fastapi import Depends

@router.get("/api/quiz/{token}/results")
async def get_quiz_results(token: str, user = Depends(get_current_user)):
    res = supabase.table("quizzes").select("id, artifacts(session_id)").eq("share_token", token).execute()
    if not res.data:
        raise HTTPException(status_code=404)
        
    db_quiz_id = res.data[0]["id"]
    session_id = res.data[0].get("artifacts", {}).get("session_id")
    
    if session_id and not user_owns_session(user.id, session_id):
        raise HTTPException(status_code=403, detail="Forbidden")
        
    results = supabase.table("quiz_responses").select("*").eq("quiz_id", db_quiz_id).execute()
    return results.data
