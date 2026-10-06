"""
SignVista — Progress Route

GET /api/progress/{sessionId}
GET /api/progress/{sessionId}/next

Ayush: Use this for the learning progress page and mastery tracking.
"""

from fastapi import APIRouter, Depends

from app.dependencies import get_current_user, require_own_session
from app.schemas import DictionaryEntry, LearningPathResponse, ProgressResponse, ProgressWordDetail
from app.session_store import get_session
from ml.inference import get_recognizable_words
from ml.sign_demos import SIGN_DEMOS, media_url
from ml.vocabulary import WORD_LIST, get_display_name

router = APIRouter(prefix="/api/progress", tags=["Progress"])


def get_mastery_tier(proficiency: float) -> str:
    if proficiency >= 95:
        return "Master"
    if proficiency >= 80:
        return "Advanced"
    if proficiency >= 60:
        return "Intermediate"
    if proficiency >= 30:
        return "Beginner"
    return "Novice"


@router.get("/{session_id}", response_model=ProgressResponse)
def get_progress(session_id: str, current_user: dict = Depends(get_current_user)):
    """
    Get detailed learning progress and breakdown for the user.
    """
    require_own_session(current_user, session_id)

    session = get_session(session_id)
    learn_stats = session.learn.get_stats()

    word_details = []
    total_mastered = 0

    words = list(dict.fromkeys([w.lower() for w in get_recognizable_words()] + list(learn_stats.keys()))) or WORD_LIST
    for word_key in words:
        stats = learn_stats.get(word_key, {"attempts": 0, "correct": 0, "proficiency": 0.0})
        proficiency = stats["proficiency"]
        tier = get_mastery_tier(proficiency)

        if proficiency >= 80:
            total_mastered += 1

        word_details.append(ProgressWordDetail(
            word=word_key,
            display_name=get_display_name(word_key),
            proficiency=proficiency,
            attempts=stats["attempts"],
            correct=stats["correct"],
            mastery_tier=tier
        ))

    return ProgressResponse(
        sessionId=session_id,
        overall_proficiency=session.learn.get_overall_proficiency(),
        words_practiced=session.learn.get_words_practiced(),
        total_mastered=total_mastered,
        word_details=word_details
    )


@router.get("/{session_id}/next", response_model=LearningPathResponse)
def get_learning_path(session_id: str, current_user: dict = Depends(get_current_user)):
    """
    Suggest the next 3 words to practice based on current proficiency.
    Priority: lowest proficiency (>0) first, then unpracticed words.
    """
    require_own_session(current_user, session_id)

    session = get_session(session_id)
    learn_stats = session.learn.get_stats()

    # Calculate weighted priority for each word
    priorities = []
    pool = [w.lower() for w in get_recognizable_words()] or WORD_LIST
    for word_key in pool:
        stats = learn_stats.get(word_key)
        if stats:
            # Low proficiency (but started) gets priority
            priority = stats["proficiency"]
        else:
            # Unpracticed is also priority
            priority = 0.0
        priorities.append((word_key, priority))

    # Sort by priority ascending (lowest proficiency first)
    # But let's prioritize words with some attempts first to "fix" them
    priorities.sort(key=lambda x: (x[1] == 0, x[1]))

    suggested_keys = [p[0] for p in priorities[:3]]
    suggested_words = []

    for word_key in suggested_keys:
        demo = SIGN_DEMOS.get(word_key, {})
        suggested_words.append(DictionaryEntry(
            word=word_key,
            display_name=get_display_name(word_key),
            hindi_name=demo.get("hindi_name", ""),
            category=demo.get("category", "common"),
            difficulty=demo.get("difficulty", "easy"),
            gif_url=media_url(demo.get("gif_url", "")),
            description=demo.get("description", ""),
            tips=demo.get("tips", [])
        ))

    return LearningPathResponse(suggested_words=suggested_words)
