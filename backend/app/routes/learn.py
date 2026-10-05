"""
SignVista — Learn Route

POST /api/learn/attempt — practice a specific sign and get proficiency feedback.

The client streams frames for the target sign. Frames are buffered until the
pipeline produces a result; only then is an attempt recorded (so empty frames,
missing hands or a still-filling buffer never count as failed attempts).
After each recorded attempt the buffer restarts, so one attempt = one sign.
"""

import logging
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_current_user, require_own_session
from app.schemas import LearnAttemptRequest, LearnAttemptResponse
from app.session_store import get_session
from app.utils.frame_pipeline import throttle
from app.utils.frame_utils import FrameDecodeError, decode_base64_frame, resize_frame, validate_frame
from ml.inference import is_recognizable, is_relevant_prediction, predict_from_raw_frame, reset_buffer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/learn", tags=["Learn"])

STATUS_MESSAGES = {
    "no_face": "Make sure your face is visible to the camera.",
    "no_hands": "Raise your hands into the frame to start signing.",
    "no_model": "Sign recognition is unavailable right now.",
    "landmarks_unavailable": "Sign recognition is unavailable right now.",
    "throttled": "",
}


@router.post("/attempt", response_model=LearnAttemptResponse)
def learn_attempt(request: LearnAttemptRequest, current_user: Dict = Depends(get_current_user)):
    """Submit a frame while practicing `targetWord`."""
    if request.sessionId:
        require_own_session(current_user, request.sessionId)
    user_id = current_user["user_id"]
    target = request.targetWord.strip()

    if not is_recognizable(target):
        raise HTTPException(
            status_code=400,
            detail=f"'{target}' can't be practiced with the camera yet. "
                   "Use GET /api/vocabulary and pick a word with recognizable=true.",
        )

    session = get_session(user_id)
    word_stats = session.learn.get_stats().get(target.lower(), {})

    def pending(message: str) -> LearnAttemptResponse:
        return LearnAttemptResponse(
            predicted=None, correct=False,
            proficiency=word_stats.get("proficiency", 0.0),
            attempts=word_stats.get("attempts", 0),
            correct_count=word_stats.get("correct", 0),
            fault=message, confidence=0.0,
        )

    ml_key = f"{user_id}:learn"
    if not throttle.allow(ml_key):
        return pending("")

    try:
        frame = decode_base64_frame(request.frame)
    except FrameDecodeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not validate_frame(frame):
        raise HTTPException(status_code=400, detail="Invalid frame")
    frame = resize_frame(frame, target_width=640)

    predicted, confidence, status, _, _ = predict_from_raw_frame(session_id=ml_key, frame=frame)

    if status.startswith("collecting"):
        return pending(f"Keep signing... {status.split('_')[-1]}")
    if status in STATUS_MESSAGES:
        return pending(STATUS_MESSAGES[status])
    if predicted is None or not is_relevant_prediction(target, predicted):
        # No confident word-level sign yet — keep watching instead of failing the user
        return pending("Hold the sign clearly...")

    result = session.learn.record_attempt(
        target_word=target,
        predicted_word=predicted,
        confidence=confidence,
        user_session=session,
    )
    reset_buffer(ml_key)

    return LearnAttemptResponse(
        predicted=predicted,
        correct=result["correct"],
        proficiency=result["proficiency"],
        attempts=result["attempts"],
        correct_count=result["correct_count"],
        fault=result["fault"],
        confidence=round(confidence, 3),
    )
