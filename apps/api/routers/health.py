from fastapi import APIRouter
from qdrant_client import QdrantClient
from agent.llm import get_provider_status

router = APIRouter()

@router.get("/api/health")
def health():
    return {
        "status": "ok",
        "llm_providers": get_provider_status()
    }

@router.get("/api/health/qdrant")
def qdrant_health():
    try:
        client = QdrantClient(url="http://localhost:6333")
        client.get_collections()
        return {"status": "ok", "message": "Qdrant is accessible"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
