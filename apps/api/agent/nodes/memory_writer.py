from agent.state import AppState
from langfuse.decorators import observe
from supabase import create_client, Client
import os

supabase: Client = create_client(
    os.getenv("SUPABASE_URL", "http://localhost:8000"),
    os.getenv("SUPABASE_SERVICE_KEY", os.getenv("SUPABASE_ANON_KEY", ""))
)

@observe()
async def memory_writer_node(state: AppState):
    session_id = state.get("session_id")
    prompt = state.get("prompt")
    modes = state.get("modes", [])
    
    messages = state.get("messages", [])
    if len(messages) > 0 and session_id:
        # The last message is from the assistant
        ai_msg = messages[-1].content
        
        try:
            supabase.table("messages").insert([
                {
                    "session_id": session_id,
                    "role": "user",
                    "content": prompt,
                    "modes": modes
                },
                {
                    "session_id": session_id,
                    "role": "assistant",
                    "content": ai_msg,
                    "modes": modes
                }
            ]).execute()
        except Exception as e:
            print(f"Error saving messages: {e}")
            
    return {}
