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
    res = supabase.table("quizzes").select("id").eq("share_token", token).execute()
    if not res.data:
        raise HTTPException(status_code=404)
        
    db_quiz_id = res.data[0]["id"]
    
    supabase.table("quiz_responses").insert({
        "quiz_id": db_quiz_id,
        "respondent_name": req.respondent_name,
        "answers": req.answers,
        "score": req.score,
        "per_topic": req.per_topic
    }).execute()
    
    return {"status": "success"}
    
@router.get("/api/quiz/{token}/results")
async def get_quiz_results(token: str):
    res = supabase.table("quizzes").select("id").eq("share_token", token).execute()
    if not res.data:
        raise HTTPException(status_code=404)
        
    db_quiz_id = res.data[0]["id"]
    results = supabase.table("quiz_responses").select("*").eq("quiz_id", db_quiz_id).execute()
    return results.data
