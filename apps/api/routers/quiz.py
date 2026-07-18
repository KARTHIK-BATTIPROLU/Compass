import json
import time
from collections import defaultdict
from fastapi import APIRouter, HTTPException, Request
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

# ── Public quiz-submit abuse guards ──────────────────────────────────────────
# In-memory sliding-window counters. Single-process only: this resets on
# restart and doesn't share state across workers/replicas — acceptable for
# the current single-instance deployment, noted in DECISIONS.md.
_RATE_WINDOW_SECONDS = 60
_MAX_PER_IP = 10
_MAX_PER_TOKEN = 10
_MAX_NAME_LEN = 80
_MAX_ANSWERS_BYTES = 20 * 1024

_ip_hits: Dict[str, list] = defaultdict(list)
_token_hits: Dict[str, list] = defaultdict(list)

def _check_rate_limit(store: Dict[str, list], key: str, limit: int) -> bool:
    """Returns True if the request is allowed, False if it should be throttled."""
    now = time.time()
    hits = store[key]
    cutoff = now - _RATE_WINDOW_SECONDS
    while hits and hits[0] < cutoff:
        hits.pop(0)
    if len(hits) >= limit:
        return False
    hits.append(now)
    return True

@router.get("/api/quiz/{token}")
async def get_quiz(token: str):
    res = supabase.table("quizzes").select("*").eq("share_token", token).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return res.data[0]

@router.post("/api/quiz/{token}/submit")
async def submit_quiz(token: str, request: Request):
    client_ip = request.client.host if request.client else "unknown"

    if not _check_rate_limit(_ip_hits, client_ip, _MAX_PER_IP):
        raise HTTPException(status_code=429, detail="Too many submissions from this device — please wait a minute and try again.")
    if not _check_rate_limit(_token_hits, token, _MAX_PER_TOKEN):
        raise HTTPException(status_code=429, detail="This quiz is getting a lot of submissions right now — please wait a minute and try again.")

    try:
        body = await request.json()
        if not isinstance(body, dict):
            raise ValueError("body must be a JSON object")
    except Exception:
        raise HTTPException(status_code=400, detail="Malformed request body — expected a JSON object.")

    respondent_name = body.get("respondent_name")
    answers = body.get("answers")
    score = body.get("score")
    per_topic = body.get("per_topic")

    if not isinstance(respondent_name, str) or not respondent_name.strip():
        raise HTTPException(status_code=400, detail="respondent_name is required.")
    if len(respondent_name) > _MAX_NAME_LEN:
        raise HTTPException(status_code=400, detail=f"respondent_name must be {_MAX_NAME_LEN} characters or fewer.")
    if not isinstance(answers, dict):
        raise HTTPException(status_code=400, detail="answers must be an object.")
    if len(json.dumps(answers)) > _MAX_ANSWERS_BYTES:
        raise HTTPException(status_code=400, detail="answers payload is too large.")
    if not isinstance(score, (int, float)):
        raise HTTPException(status_code=400, detail="score must be a number.")
    if not isinstance(per_topic, dict):
        raise HTTPException(status_code=400, detail="per_topic must be an object.")

    req = QuizResponse(
        quiz_id=str(body.get("quiz_id", "")),
        respondent_name=respondent_name,
        answers=answers,
        score=int(score),
        per_topic=per_topic,
    )

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
