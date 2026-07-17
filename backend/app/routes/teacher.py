from collections import defaultdict

from fastapi import APIRouter, Depends

from app.auth.models import Role, UserPublic
from app.auth.routes import require_role
from app.db.mongo_client import get_db

router = APIRouter(prefix="/teacher", tags=["teacher"])


@router.get("/class-weak-spots")
async def class_weak_spots(user: UserPublic = Depends(require_role(Role.TEACHER))):
    """Aggregate weak spots across students (optionally linked via teacher_id)."""
    db = get_db()
    students = []
    async for s in db.users.find({"role": "student"}):
        teacher_id = s.get("teacher_id")
        if teacher_id is None or teacher_id == user.id:
            students.append(str(s["_id"]))
    # Demo fallback: if no linked students, aggregate all students
    if not students:
        async for s in db.users.find({"role": "student"}):
            students.append(str(s["_id"]))

    agg: dict[str, dict] = defaultdict(
        lambda: {"concept": "", "topic": "", "total_failures": 0, "students": 0}
    )
    async for doc in db.weak_spots.find({"user_id": {"$in": students}}):
        key = doc.get("concept") or doc.get("topic") or "unknown"
        bucket = agg[key]
        bucket["concept"] = doc.get("concept")
        bucket["topic"] = doc.get("topic")
        bucket["total_failures"] += int(doc.get("failure_count") or 0)
        bucket["students"] += 1

    items = sorted(agg.values(), key=lambda x: x["total_failures"], reverse=True)
    return {"class_weak_spots": items, "student_count": len(students)}


@router.post("/link-student/{student_id}")
async def link_student(student_id: str, user: UserPublic = Depends(require_role(Role.TEACHER))):
    db = get_db()
    result = await db.users.update_one(
        {"_id": student_id, "role": "student"},
        {"$set": {"teacher_id": user.id}},
    )
    return {"ok": result.modified_count > 0 or result.matched_count > 0}
