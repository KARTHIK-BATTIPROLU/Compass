from collections import defaultdict
from typing import Any

from fastapi import APIRouter, Depends

from app.auth.models import Role, UserPublic
from app.auth.routes import require_role
from app.db.mongo_client import get_db

router = APIRouter(prefix="/student", tags=["student"])


@router.get("/weak-spots")
async def get_weak_spots(user: UserPublic = Depends(require_role(Role.STUDENT))):
    db = get_db()
    cursor = db.weak_spots.find({"user_id": user.id}).sort("failure_count", -1)
    items = []
    async for doc in cursor:
        items.append(
            {
                "id": str(doc["_id"]),
                "topic": doc.get("topic"),
                "concept": doc.get("concept"),
                "failure_count": doc.get("failure_count", 0),
                "last_attempt_correct": doc.get("last_attempt_correct", False),
                "last_strategy": doc.get("last_strategy"),
                "last_updated": doc.get("last_updated"),
            }
        )
    return {"weak_spots": items}


@router.get("/generated-docs")
async def get_generated_docs(user: UserPublic = Depends(require_role(Role.STUDENT, Role.TEACHER))):
    db = get_db()
    cursor = db.generated_docs.find({"user_id": user.id}).sort("created_at", -1).limit(50)
    items = []
    async for doc in cursor:
        items.append(
            {
                "id": str(doc["_id"]),
                "content_type": doc.get("content_type"),
                "status": doc.get("status"),
                "created_at": doc.get("created_at"),
                "content": doc.get("content"),
            }
        )
    return {"docs": items}
