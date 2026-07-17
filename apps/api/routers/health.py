from fastapi import APIRouter
from qdrant_client import QdrantClient

router = APIRouter()

@router.get("/api/health/qdrant")
def qdrant_health():
    try:
        client = QdrantClient(url="http://localhost:6333")
        client.get_collections()
        return {"status": "ok", "message": "Qdrant is accessible"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
