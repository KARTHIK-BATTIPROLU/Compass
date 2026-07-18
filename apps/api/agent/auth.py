import os
import logging
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

def get_supabase():
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_SERVICE_KEY", os.getenv("SUPABASE_ANON_KEY", ""))
    if url and key:
        from supabase import create_client
        return create_client(url, key)
    return None

async def verify_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """FastAPI dependency to verify Supabase JWT."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing authorization header")
        
    token = credentials.credentials
    sb = get_supabase()
    if not sb:
        logger.error("Supabase not configured in environment variables.")
        raise HTTPException(status_code=500, detail="Auth not configured")
        
    try:
        res = sb.auth.get_user(token)
        if not res or not res.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return res.user
    except Exception as e:
        logger.warning(f"Auth verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(request: Request, user=Depends(verify_user)):
    return user

def user_owns_session(user_id: str, session_id: str) -> bool:
    """Checks if the given user owns the session or is a teacher with access."""
    sb = get_supabase()
    if not sb:
        return False
    try:
        # Check if the user is the direct owner
        res = sb.table("sessions").select("user_id").eq("id", session_id).single().execute()
        if res.data and res.data.get("user_id") == user_id:
            return True
        
        # Check if user is a teacher (faculty role)
        user_res = sb.table("users").select("role").eq("id", user_id).single().execute()
        if user_res.data and user_res.data.get("role") == "faculty":
            return True
            
        return False
    except Exception as e:
        logger.error(f"Error checking session ownership: {e}")
        return False
