import logging
from datetime import datetime, timezone
from typing import Any, Optional

from app.agent.state import AgentState
from app.db.mongo_client import get_db

logger = logging.getLogger(__name__)

STRATEGY_CYCLE = ["text-based", "example-based", "visual-based", "analogy-based"]


def next_strategy(previous: Optional[str]) -> str:
    if not previous or previous not in STRATEGY_CYCLE:
        return "example-based"
    idx = STRATEGY_CYCLE.index(previous)
    return STRATEGY_CYCLE[(idx + 1) % len(STRATEGY_CYCLE)]


async def update_weak_spot(
    user_id: str,
    topic: str,
    concept: str,
    correct: bool,
) -> dict[str, Any]:
    db = get_db()
    now = datetime.now(timezone.utc)
    existing = await db.weak_spots.find_one({"user_id": user_id, "concept": concept})
    if existing:
        failure_count = existing.get("failure_count", 0)
        last_strategy = existing.get("last_strategy")
        if correct:
            failure_count = max(0, failure_count - 1)
        else:
            failure_count += 1
            last_strategy = next_strategy(last_strategy)
        await db.weak_spots.update_one(
            {"_id": existing["_id"]},
            {
                "$set": {
                    "topic": topic,
                    "failure_count": failure_count,
                    "last_attempt_correct": correct,
                    "last_strategy": last_strategy,
                    "last_updated": now,
                }
            },
        )
        return {
            "user_id": user_id,
            "topic": topic,
            "concept": concept,
            "failure_count": failure_count,
            "last_attempt_correct": correct,
            "last_strategy": last_strategy,
            "force_reexplain": failure_count >= 2 and not correct,
            "force_reexplain_strategy": last_strategy if failure_count >= 2 and not correct else None,
        }

    failure_count = 0 if correct else 1
    strategy = None if correct else "text-based"
    doc = {
        "user_id": user_id,
        "topic": topic,
        "concept": concept,
        "failure_count": failure_count,
        "last_attempt_correct": correct,
        "last_strategy": strategy,
        "last_updated": now,
    }
    await db.weak_spots.insert_one(doc)
    return {
        "user_id": user_id,
        "topic": topic,
        "concept": concept,
        "failure_count": failure_count,
        "last_attempt_correct": correct,
        "last_strategy": strategy,
        "force_reexplain": False,
        "force_reexplain_strategy": None,
    }


async def load_weak_spot_context(user_id: str, topic_hint: str = "") -> Optional[dict[str, Any]]:
    db = get_db()
    query: dict[str, Any] = {"user_id": user_id, "failure_count": {"$gte": 2}}
    if topic_hint:
        query["$or"] = [
            {"topic": {"$regex": topic_hint, "$options": "i"}},
            {"concept": {"$regex": topic_hint, "$options": "i"}},
        ]
    doc = await db.weak_spots.find_one(query, sort=[("failure_count", -1), ("last_updated", -1)])
    if not doc:
        return None
    return {
        "topic": doc.get("topic"),
        "concept": doc.get("concept"),
        "failure_count": doc.get("failure_count"),
        "last_strategy": doc.get("last_strategy"),
        "force_reexplain_strategy": next_strategy(doc.get("last_strategy")),
    }


async def weak_spot_tracker(state: AgentState) -> dict[str, Any]:
    """Enrich state with weak-spot driven re-explain strategy before generation."""
    user_id = state.get("user_id")
    if not user_id:
        return {}
    ctx = await load_weak_spot_context(user_id, state.get("user_input", ""))
    if not ctx:
        return {"weak_spot_context": None}
    return {
        "weak_spot_context": ctx,
        "force_reexplain_strategy": ctx.get("force_reexplain_strategy"),
        "messages": [
            {
                "role": "system",
                "content": (
                    f"Student failed {ctx.get('concept')} {ctx.get('failure_count')} times; "
                    f"use {ctx.get('force_reexplain_strategy')} approach"
                ),
            }
        ],
    }
