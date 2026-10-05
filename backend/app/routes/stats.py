"""
SignVista — Stats Route

GET /api/stats/{sessionId}
Returns complete learning statistics for a session.

Ayush: Use this for the profile/stats page with charts.
"""

import logging

from fastapi import APIRouter, Depends

from app.schemas import SessionStatsResponse, WordStats
from app.session_store import get_session
from app.dependencies import get_current_user, require_own_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Stats"])


@router.get("/stats/{session_id}", response_model=SessionStatsResponse)
def get_stats(session_id: str, current_user: dict = Depends(get_current_user)):
    """
    Get complete learning & game statistics for a session.

    Returns per-word stats (attempts, correct, proficiency) plus
    overall summary (total attempts, games played, best score).

    Ayush calls: GET /api/stats/user-123

    Response:
    ```json
    {
        "sessionId": "user-123",
        "words": {
            "hello": {"attempts": 10, "correct": 9, "proficiency": 90.0},
            "water": {"attempts": 5, "correct": 3, "proficiency": 60.0}
        },
        "total_attempts": 15,
        "total_correct": 12,
        "overall_proficiency": 75.0,
        "words_practiced": 2,
        "games_played": 3,
        "best_game_score": 450
    }
    ```
    """
    require_own_session(current_user, session_id)

    session = get_session(session_id)
    learn_stats = session.learn.get_stats()

    # Build per-word stats
    words = {}
    total_attempts = 0
    total_correct = 0

    for word_key, stats in learn_stats.items():
        words[word_key] = WordStats(
            attempts=stats["attempts"],
            correct=stats["correct"],
            proficiency=stats["proficiency"],
        )
        total_attempts += stats["attempts"]
        total_correct += stats["correct"]

    return SessionStatsResponse(
        sessionId=session_id,
        words=words,
        total_attempts=total_attempts,
        total_correct=total_correct,
        overall_proficiency=session.learn.get_overall_proficiency(),
        words_practiced=session.learn.get_words_practiced(),
        games_played=session.games_played,
        best_game_score=session.best_game_score,
    )
