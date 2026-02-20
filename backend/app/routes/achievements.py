"""
SignVista — Achievements Route

GET /api/achievements/{sessionId}

Ayush: Use this for the trophies/badges page.
"""

from fastapi import APIRouter, HTTPException
from typing import List

from app.schemas import AchievementsResponse, AchievementInfo
from app.session_store import get_session, ACHIEVEMENT_DEFINITIONS

router = APIRouter(prefix="/api/achievements", tags=["Achievements"])


@router.get("/{session_id}", response_model=AchievementsResponse)
async def get_achievements(session_id: str):
    """
    Get all available achievements and their unlocked status for the user.
    """
    session = get_session(session_id)
    unlocked = session.unlocked_achievements
    
    achievement_info_list = []
    
    for defn in ACHIEVEMENT_DEFINITIONS:
        is_unlocked = defn["id"] in unlocked
        achievement_info_list.append(AchievementInfo(
            id=defn["id"],
            name=defn["name"],
            description=defn["desc"],
            unlocked=is_unlocked,
            unlocked_at=None # We don't track the exact time of unlock yet
        ))
        
    return AchievementsResponse(
        sessionId=session_id,
        total_unlocked=len(unlocked),
        achievements=achievement_info_list
    )
