from agent.state import AppState
from supabase import create_client, Client
from qdrant_client import QdrantClient
from langchain_qdrant import QdrantVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os
from langfuse.decorators import observe

supabase: Client = create_client(
    os.getenv("SUPABASE_URL", "http://localhost:8000"),
    os.getenv("SUPABASE_SERVICE_KEY", os.getenv("SUPABASE_ANON_KEY", ""))
)

# Setup Qdrant
qdrant_client = QdrantClient(url="http://localhost:6333")
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
vector_store = QdrantVectorStore(
    client=qdrant_client,
    collection_name="curriculum",
    embedding=embeddings,
)

@observe()
async def context_loader_node(state: AppState) -> AppState:
    """
    Pulls user profile and session context into state. Also retrieves curriculum RAG context.
    """
    session_id = state.get("session_id")
    prompt = state.get("prompt", "")
    modes = state.get("modes", [])
    
    user_info = {}
    class_level = None
    curriculum_ctx = []
    
    if session_id:
        try:
            session_res = supabase.table("sessions").select("*").eq("id", session_id).execute()
            if session_res.data:
                session = session_res.data[0]
                user_id = session.get("user_id")
                class_level = session.get("class_level")
                
                user_res = supabase.table("users").select("*").eq("id", user_id).execute()
                if user_res.data:
                    user = user_res.data[0]
                    role = user.get("role")
                    
                    user_info = {
                        "role": role,
                        "region": user.get("region"),
                        "language": user.get("language"),
                        "standard": user.get("standard")
                    }
                    
                    if role == "learner":
                        weak_res = supabase.table("weakness_profiles").select("*").eq("user_id", user_id).execute()
                        user_info["weakness_profile"] = weak_res.data if weak_res.data else []
        except Exception as e:
            print(f"Error loading context: {e}")
            
    if "Curriculum" in modes or "curriculum" in [m.lower() for m in modes]:
        try:
            # Simple top-k retrieval based on prompt
            docs = await vector_store.asimilarity_search(prompt, k=3)
            curriculum_ctx = [{"content": doc.page_content, "metadata": doc.metadata} for doc in docs]
        except Exception as e:
            print(f"Qdrant retrieval error: {e}")
            
    return {
        "user": user_info,
        "class_level": class_level,
        "curriculum_ctx": curriculum_ctx
    }
