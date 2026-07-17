from agent.state import AppState
from langfuse import observe
import os
import logging

logger = logging.getLogger(__name__)

# ── Lazy Supabase client ────────────────────────────────────────────────────
_supabase = None

def get_supabase():
    global _supabase
    if _supabase is None:
        from supabase import create_client
        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_SERVICE_KEY", os.getenv("SUPABASE_ANON_KEY", ""))
        if url and key:
            _supabase = create_client(url, key)
        else:
            logger.warning("Supabase credentials missing — context_loader will return empty context.")
    return _supabase


# ── Lazy Qdrant / vector store ──────────────────────────────────────────────
_vector_store = None

def get_vector_store():
    """Returns a QdrantVectorStore or None if Qdrant is unreachable."""
    global _vector_store
    if _vector_store is not None:
        return _vector_store
    try:
        from qdrant_client import QdrantClient
        from langchain_qdrant import QdrantVectorStore
        from langchain_google_genai import GoogleGenerativeAIEmbeddings

        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        client = QdrantClient(url=qdrant_url, timeout=3)
        # Quick connectivity check
        client.get_collections()

        embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
        _vector_store = QdrantVectorStore(
            client=client,
            collection_name="curriculum_chunks",
            embedding=embeddings,
        )
        logger.info("Qdrant connected successfully.")
        return _vector_store
    except Exception as e:
        logger.warning(f"Qdrant unavailable — curriculum RAG disabled: {e}")
        return None


@observe()
async def context_loader_node(state: AppState) -> AppState:
    """
    Pulls user profile and session context into state.
    Also retrieves curriculum RAG context for faculty turns.
    Gracefully degrades if Supabase or Qdrant is unavailable.
    """
    session_id = state.get("session_id")
    prompt = state.get("prompt", "")
    modes = state.get("modes", [])

    user_info = {}
    class_level = None
    curriculum_ctx = []
    weakness_ctx = None

    supabase = get_supabase()

    if supabase and session_id:
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
                        "standard": user.get("standard"),
                    }

                    if role == "learner":
                        weak_res = (
                            supabase.table("weakness_profiles")
                            .select("*")
                            .eq("user_id", user_id)
                            .execute()
                        )
                        if weak_res.data:
                            weakness_ctx = {
                                "identified_topics": [
                                    r.get("topic_id", "") for r in weak_res.data
                                ]
                            }
        except Exception as e:
            logger.error(f"Error loading session/user context: {e}")

    # Retrieve curriculum chunks for EVERY faculty generation (not just Curriculum chip)
    is_faculty = user_info.get("role") == "faculty"
    if is_faculty and prompt:
        vs = get_vector_store()
        if vs:
            try:
                docs = await vs.asimilarity_search(prompt, k=4)
                curriculum_ctx = [
                    {"content": doc.page_content, "metadata": doc.metadata}
                    for doc in docs
                ]
            except Exception as e:
                logger.warning(f"Qdrant curriculum retrieval failed: {e}")

    return {
        "user": user_info,
        "class_level": class_level,
        "curriculum_ctx": curriculum_ctx,
        "weakness_ctx": weakness_ctx,
    }
