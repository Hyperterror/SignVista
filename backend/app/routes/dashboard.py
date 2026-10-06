"""
SignVista — Dashboard Route

GET /api/dashboard/{sessionId}

Ayush: The ultimate personalized dashboard endpoint.
       Call this when the user lands on the dashboard.
"""

from fastapi import APIRouter, Depends

from app.dependencies import get_current_user, require_own_session
from app.routes.history import format_activity_desc, format_activity_title
from app.schemas import ActivityEvent, DashboardResponse, XPLevelInfo
from app.session_store import ACHIEVEMENT_DEFINITIONS, USER_LEVEL_THRESHOLDS, get_session
from ml.inference import get_recognizable_words
from ml.vocabulary import WORD_LIST

router = APIRouter(prefix="/api", tags=["Dashboard"])


@router.get("/dashboard/{session_id}", response_model=DashboardResponse)
def get_dashboard(session_id: str, current_user: dict = Depends(get_current_user)):
    """
    Get aggregated dashboard summary.
    """
    require_own_session(current_user, session_id)

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
            description=format_activity_desc(h["type"], h["data"]),
            xp_earned=h.get("xp_earned", 0),
        ))

    # Mastery stats
    total_mastered = 0
    for stats in session.learn.word_stats.values():
        if stats["proficiency"] >= 80:
            total_mastered += 1

    # Learning path (simple suggest)
    practiced = session.learn.word_stats.keys()
    pool = get_recognizable_words() or WORD_LIST
    unpracticed = [w for w in pool if w.lower() not in practiced]
    suggested = unpracticed[:3] if unpracticed else pool[:3]

    return DashboardResponse(
        sessionId=session_id,
        user_name=current_user.get("name") or "User",
        xp_info=xp_info,
        overall_proficiency=session.learn.get_overall_proficiency(),
        words_practiced=len(practiced),
        words_mastered=total_mastered,
        current_streak=session.current_streak,
        longest_streak=session.longest_streak,
        recent_activity=recent,
        total_achievements=len(ACHIEVEMENT_DEFINITIONS),
        unlocked_achievements_count=len(session.unlocked_achievements),
        best_game_score=session.best_game_score,
        suggested_next_words=suggested
    )
