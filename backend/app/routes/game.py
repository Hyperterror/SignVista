"""
SignVista — Game Routes

POST /api/game/start      — Start a new game round
POST /api/game/attempt     — Submit a sign during game
GET  /api/game/result/{sessionId}/{gameId} — Get final results

Ayush: Start a game → get challenges → submit frames → show final score.
       Score = 100 points × streak multiplier per correct sign.
       Badges are automatically calculated based on performance.
"""

import logging

from fastapi import APIRouter, HTTPException

from app.schemas import (
    GameStartRequest,
    GameStartResponse,
    GameAttemptRequest,
    GameAttemptResponse,
    GameResultResponse,
)
from app.session_store import get_session
from app.utils.frame_utils import decode_base64_frame, validate_frame, resize_frame, FrameDecodeError
from ml.inference import predict_from_raw_frame
from ml.vocabulary import WORD_DISPLAY

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/game", tags=["Game"])


@router.post("/start", response_model=GameStartResponse)
async def start_game(request: GameStartRequest):
    """
    Initialize a new game round.

    Creates a shuffled queue of challenge words and returns the first one.

    Ayush sends:
    ```json
    {
        "sessionId": "user-123",
        "duration": 30
    }
    ```
    """
    if not request.sessionId or not request.sessionId.strip():
        raise HTTPException(status_code=400, detail="sessionId is required")

    session = get_session(request.sessionId)
    game = session.start_game(duration=request.duration)

    return GameStartResponse(
        gameId=game.game_id,
        currentChallenge=WORD_DISPLAY.get(game.current_challenge, game.current_challenge),
        duration=game.duration,
        totalChallenges=len(game.challenges),
    )


@router.post("/attempt", response_model=GameAttemptResponse)
async def game_attempt(request: GameAttemptRequest):
    """
    Submit a sign during an active game.

    If correct → score increases, streak grows, next challenge appears.
    If wrong → streak resets, same challenge stays.

    Ayush sends:
    ```json
    {
        "sessionId": "user-123",
        "gameId": "a1b2c3d4",
        "frame": "data:image/jpeg;base64,..."
    }
    ```
    """
    if not request.sessionId or not request.sessionId.strip():
        raise HTTPException(status_code=400, detail="sessionId is required")

    session = get_session(request.sessionId)
    game = session.get_game(request.gameId)

    if game is None:
        raise HTTPException(status_code=404, detail=f"Game '{request.gameId}' not found. Start a new game first.")

    if not game.is_active or game.is_expired:
        game.is_active = False
        session.finish_game(request.gameId)
        raise HTTPException(
            status_code=400,
            detail="Game has ended. Call GET /api/game/result to see your score."
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
        session_id=f"{request.sessionId}_game_{request.gameId}",
        frame=frame,
    )

    # Record attempt
    result = game.record_attempt(predicted, confidence)

    # Get display name for current challenge
    current_display = WORD_DISPLAY.get(
        result["currentChallenge"], result["currentChallenge"]
    )

    return GameAttemptResponse(
        predicted=result["predicted"],
        correct=result["correct"],
        currentChallenge=current_display,
        score=result["score"],
        streak=result["streak"],
        multiplier=result["multiplier"],
        wordsCompleted=result["wordsCompleted"],
        confidence=round(confidence, 3),
    )


@router.get("/result/{session_id}/{game_id}", response_model=GameResultResponse)
async def game_result(session_id: str, game_id: str):
    """
    Get final results for a completed game.

    Returns score, accuracy, badges, and per-word breakdown.

    Ayush calls: GET /api/game/result/user-123/a1b2c3d4
    """
    session = get_session(session_id)
    game = session.get_game(game_id)

    if game is None:
        raise HTTPException(status_code=404, detail=f"Game '{game_id}' not found")

    # Finalize game
    session.finish_game(game_id)

    return GameResultResponse(**game.get_final_result())
