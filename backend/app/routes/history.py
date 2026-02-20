"""
SignVista — History Route

GET /api/history/{sessionId}

Ayush: Use this for the activity timeline.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List

from app.schemas import HistoryResponse, ActivityEvent
from app.session_store import get_session

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
        aid = data.get("id", "Unknown")
        return f"Congratulations! You've unlocked the '{aid}' achievement."
    if activity_type == "level_up":
        old = data.get("old", 1)
        new = data.get("new", 2)
        return f"Reached Level {new} from Level {old}!"
    if activity_type == "game_started":
        return f"Started game session {data.get('gameId', '')}"
    return "Generic activity"


@router.get("/{session_id}", response_model=HistoryResponse)
async def get_history(
    session_id: str,
    limit: int = Query(20, ge=1, le=100),
    type: Optional[str] = None
):
    """
    Get session activity history with formatting for display.
    """
    session = get_session(session_id)
    raw_history = session.activity_history[::-1]  # Newest first
    
    events = []
    for h in raw_history:
        if type and h["type"] != type:
            continue
            
        events.append(ActivityEvent(
            type=h["type"],
            timestamp=h["timestamp"],
            title=format_activity_title(h["type"], h["data"]),
            description=format_activity_desc(h["type"], h["data"]),
            xp_earned=0 # XP award info isn't stored per-activity yet, but could be added
        ))
        
        if len(events) >= limit:
            break
            
    return HistoryResponse(
        sessionId=session_id,
        activities=events
    )
