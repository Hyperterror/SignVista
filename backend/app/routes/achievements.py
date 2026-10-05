"""
SignVista — Achievements Route

GET /api/achievements/{sessionId}

Ayush: Use this for the trophies/badges page.
"""

from fastapi import APIRouter, Depends

from app.schemas import AchievementsResponse, AchievementInfo
from app.session_store import get_session, ACHIEVEMENT_DEFINITIONS
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_own_session
from app.models import ActivityLog

router = APIRouter(prefix="/api/achievements", tags=["Achievements"])


@router.get("/{session_id}", response_model=AchievementsResponse)
def get_achievements(session_id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """All achievements with unlocked status and unlock time."""
    require_own_session(current_user, session_id)

    session = get_session(session_id)
    unlocked = set(session.unlocked_achievements)

    unlocked_at = {}
    for row in db.query(ActivityLog).filter(
        ActivityLog.user_id == session_id, ActivityLog.type == "achievement_unlocked"
    ):
        aid = (row.data or {}).get("id")
        if aid and aid not in unlocked_at:
            unlocked_at[aid] = row.timestamp

    return AchievementsResponse(
        sessionId=session_id,
        total_unlocked=len(unlocked),
        achievements=[
            AchievementInfo(
                id=d["id"],
                name=d["name"],
                description=d["desc"],
                unlocked=d["id"] in unlocked,
                unlocked_at=unlocked_at.get(d["id"]) if d["id"] in unlocked else None,
            )
            for d in ACHIEVEMENT_DEFINITIONS
        ],
    )
