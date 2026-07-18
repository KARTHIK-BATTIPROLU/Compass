from fastapi import APIRouter, HTTPException, Depends
from supabase import create_client, Client
import os
from agent.auth import get_current_user, user_owns_session

router = APIRouter()
supabase: Client = create_client(
    os.getenv("SUPABASE_URL", "http://localhost:8000"),
    os.getenv("SUPABASE_SERVICE_KEY", os.getenv("SUPABASE_ANON_KEY", ""))
)

@router.get("/api/messages/{session_id}")
async def get_messages(session_id: str, user = Depends(get_current_user)):
    if not user_owns_session(user.id, session_id):
        raise HTTPException(status_code=403, detail="Forbidden")
        
    try:
        res = supabase.table("messages").select("*").eq("session_id", session_id).order("created_at", desc=False).execute()
        return res.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
