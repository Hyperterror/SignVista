"""
SignVista — Dashboard Route

GET /api/dashboard/{sessionId}

Ayush: The ultimate personalized dashboard endpoint.
       Call this when the user lands on the dashboard.
"""

from fastapi import APIRouter, HTTPException
from typing import List

from app.schemas import DashboardResponse, XPLevelInfo, ActivityEvent
from app.session_store import get_session, USER_LEVEL_THRESHOLDS
from app.routes.history import format_activity_title, format_activity_desc
from ml.vocabulary import WORD_LIST

router = APIRouter(prefix="/api", tags=["Dashboard"])


@router.get("/dashboard/{session_id}", response_model=DashboardResponse)
async def get_dashboard(session_id: str):
    """
    Get aggregated dashboard summary.
    """
    session = get_session(session_id)
    
    # Calculate XP Bar
    lvl = session.level
    current_xp = session.total_xp
    
    # XP to reach current level
    base_xp = USER_LEVEL_THRESHOLDS[lvl-1]
    
    # XP required for next level
    if lvl < len(USER_LEVEL_THRESHOLDS):
        next_xp = USER_LEVEL_THRESHOLDS[lvl]
        needed_for_next = next_xp - base_xp
        progress_in_level = current_xp - base_xp
        percent = round((progress_in_level / needed_for_next) * 100, 1)
    else:
        # Max Level
        next_xp = current_xp
        percent = 100.0

    xp_info = XPLevelInfo(
        current_xp=current_xp,
        level=lvl,
        next_level_xp=next_xp,
        progress_percent=percent
    )

    # Recent Activity (last 5)
    recent = []
    for h in session.activity_history[-5:][::-1]:
        recent.append(ActivityEvent(
            type=h["type"],
            timestamp=h["timestamp"],
            title=format_activity_title(h["type"], h["data"]),
            description=format_activity_desc(h["type"], h["data"])
        ))

    # Mastery stats
    total_mastered = 0
    for stats in session.learn.word_stats.values():
        if stats["proficiency"] >= 80:
            total_mastered += 1

    # Learning path (simple suggest)
    practiced = session.learn.word_stats.keys()
    unpracticed = [w for w in WORD_LIST if w not in practiced]
    suggested = unpracticed[:3] if unpracticed else WORD_LIST[:3]

    return DashboardResponse(
        sessionId=session_id,
        user_name="User", # Ideally fetch from profile if available
        xp_info=xp_info,
        overall_proficiency=session.learn.get_overall_proficiency(),
        words_practiced=len(practiced),
        words_mastered=total_mastered,
        current_streak=session.current_streak,
        recent_activity=recent,
        total_achievements=12,
        unlocked_achievements_count=len(session.unlocked_achievements),
        best_game_score=session.best_game_score,
        suggested_next_words=suggested
    )
