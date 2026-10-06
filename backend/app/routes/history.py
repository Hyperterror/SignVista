"""
SignVista — History Route

GET /api/history/{sessionId}

Ayush: Use this for the activity timeline.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_own_session
from app.models import ActivityLog
from app.schemas import ActivityEvent, HistoryResponse

router = APIRouter(prefix="/api/history", tags=["History"])


def format_activity_title(activity_type: str, data: dict) -> str:
    if activity_type == "learn_attempt":
        word = data.get("word", "a word")
        correct = data.get("correct", False)
        return f"Practiced '{word}'" if correct else f"Attempted '{word}'"
    if activity_type == "game_completed":
        return "Game Completed"
    if activity_type == "achievement_unlocked":
        return "Achievement Unlocked!"
    if activity_type == "level_up":
        return "Level Up!"
    if activity_type == "game_started":
        return "Started a Game"
    return "Activity"


def format_activity_desc(activity_type: str, data: dict) -> str:
    if activity_type == "learn_attempt":
        correct = data.get("correct", False)
        prof = data.get("proficiency", 0.0)
        return f"Correct! Current proficiency: {prof}%" if correct else "Incorrect sign. Keep practicing!"
    if activity_type == "game_completed":
        score = data.get("score", 0)
        acc = data.get("accuracy", 0.0)
        return f"Scored {score} points with {acc}% accuracy."
    if activity_type == "achievement_unlocked":
        from app.session_store import ACHIEVEMENTS_BY_ID
        aid = data.get("id", "Unknown")
        name = ACHIEVEMENTS_BY_ID.get(aid, {}).get("name", aid)
        return f"Congratulations! You've unlocked {name}."
    if activity_type == "level_up":
        old = data.get("old", 1)
        new = data.get("new", 2)
        return f"Reached Level {new} from Level {old}!"
    if activity_type == "game_started":
        return f"Started game session {data.get('gameId', '')}"
    return "Generic activity"


@router.get("/{session_id}", response_model=HistoryResponse)
def get_history(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Activity timeline, newest first."""
    require_own_session(current_user, session_id)

    q = db.query(ActivityLog).filter(ActivityLog.user_id == session_id)
    if type:
        q = q.filter(ActivityLog.type == type)
    rows = q.order_by(ActivityLog.timestamp.desc()).limit(limit).all()

    events = [
        ActivityEvent(
            type=r.type,
            timestamp=r.timestamp,
            title=format_activity_title(r.type, r.data or {}),
            description=format_activity_desc(r.type, r.data or {}),
            xp_earned=r.xp_earned or 0,
        )
        for r in rows
    ]
    return HistoryResponse(sessionId=session_id, activities=events)
