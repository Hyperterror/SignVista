"""
SignVista — Learn Route

POST /api/learn/attempt
Practice a specific word and get proficiency feedback.

Ayush: User selects a word from vocabulary, records their sign,
       and this endpoint compares prediction vs target.
"""

import logging

from fastapi import APIRouter, HTTPException

from app.schemas import LearnAttemptRequest, LearnAttemptResponse
from app.session_store import get_session
from app.utils.frame_utils import decode_base64_frame, validate_frame, resize_frame, FrameDecodeError
from ml.inference import predict_from_raw_frame
from ml.vocabulary import is_valid_word

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/learn", tags=["Learn"])


@router.post("/attempt", response_model=LearnAttemptResponse)
async def learn_attempt(request: LearnAttemptRequest):
    """
    Submit a practice attempt for a specific word.

    Flow:
    1. Validate targetWord is in vocabulary
    2. Run same ML inference as translate
    3. Compare predicted vs target
    4. Update proficiency stats
    5. Return feedback with fault analysis

    Ayush sends:
    ```json
    {
        "sessionId": "user-123",
        "targetWord": "hello",
        "frame": "data:image/jpeg;base64,/9j/4AAQ..."
    }
    ```
    """
    # Validate session ID
    if not request.sessionId or not request.sessionId.strip():
        raise HTTPException(status_code=400, detail="sessionId is required")

    # Validate target word
    if not is_valid_word(request.targetWord):
        raise HTTPException(
            status_code=400,
            detail=f"'{request.targetWord}' is not in the vocabulary. Use GET /api/vocabulary to see available words."
        )

    # Decode frame
    try:
        frame = decode_base64_frame(request.frame)
    except FrameDecodeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not validate_frame(frame):
        raise HTTPException(status_code=400, detail="Invalid frame")

    frame = resize_frame(frame, target_width=640)

    # Run ML inference
    predicted, confidence, buffer_status, _, _ = predict_from_raw_frame(
        session_id=request.sessionId,
        frame=frame,
    )

    # If buffer is still collecting, return partial state
    if buffer_status.startswith("collecting"):
        return LearnAttemptResponse(
            predicted=None,
            correct=False,
            proficiency=0.0,
            attempts=0,
            correct_count=0,
            fault=f"Building frame buffer... {buffer_status}",
            confidence=0.0,
        )

    # Record attempt in session
    session = get_session(request.sessionId)
    result = session.learn.record_attempt(
        target_word=request.targetWord,
        predicted_word=predicted,
        confidence=confidence,
        user_session=session,
    )

    return LearnAttemptResponse(
        predicted=predicted,
        correct=result["correct"],
        proficiency=result["proficiency"],
        attempts=result["attempts"],
        correct_count=result["correct_count"],
        fault=result["fault"],
        confidence=round(confidence, 3),
    )
