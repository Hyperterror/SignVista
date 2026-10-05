"""
SignVista — Game Routes

POST /api/game/start                         — start a new round
POST /api/game/attempt                       — submit a frame during the round
GET  /api/game/result/{sessionId}/{gameId}   — end the round (if still running) and get results

Challenges are drawn only from signs the loaded models can recognize.
Score = GAME_POINTS_PER_CORRECT × streak multiplier per correct sign.
A game is finalized (XP, history, achievements) exactly once.
"""

import logging
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_current_user, require_own_session
from app.schemas import (
    GameAttemptRequest,
    GameAttemptResponse,
    GameResultResponse,
    GameStartRequest,
    GameStartResponse,
)
from app.session_store import get_session
from app.utils.frame_pipeline import throttle
from app.utils.frame_utils import FrameDecodeError, decode_base64_frame, resize_frame, validate_frame
from ml.inference import get_game_word_pool, is_relevant_prediction, predict_from_raw_frame, reset_buffer, reset_session
from ml.vocabulary import get_display_name

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/game", tags=["Game"])


def _ml_key(user_id: str, game_id: str) -> str:
    return f"{user_id}:game:{game_id}"


@router.post("/start", response_model=GameStartResponse)
def start_game(request: GameStartRequest, current_user: Dict = Depends(get_current_user)):
    """Initialize a new game round."""
    if request.sessionId:
        require_own_session(current_user, request.sessionId)

    pool = get_game_word_pool()
    if not pool:
        raise HTTPException(status_code=503, detail="Sign recognition is unavailable, so games can't be played right now.")

    session = get_session(current_user["user_id"])
    game = session.start_game(duration=request.duration, word_pool=pool)

    return GameStartResponse(
        gameId=game.game_id,
        currentChallenge=get_display_name(game.current_challenge),
        duration=game.duration,
        totalChallenges=len(game.challenges),
    )


@router.post("/attempt", response_model=GameAttemptResponse)
def game_attempt(request: GameAttemptRequest, current_user: Dict = Depends(get_current_user)):
    """Submit a frame during an active game."""
    if request.sessionId:
        require_own_session(current_user, request.sessionId)
    user_id = current_user["user_id"]

    session = get_session(user_id)
    game = session.get_game(request.gameId)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found. Start a new game first.")

    if not game.is_active or game.is_expired or game.finished:
        session.finish_game(request.gameId)
        reset_session(_ml_key(user_id, game.game_id))
        raise HTTPException(status_code=409, detail="Game has ended. Call GET /api/game/result to see your score.")

    def respond(result: Dict, confidence: float, status: str) -> GameAttemptResponse:
        return GameAttemptResponse(
            predicted=get_display_name(result["predicted"]) if result["predicted"] else None,
            correct=result["correct"],
            currentChallenge=get_display_name(result["currentChallenge"]),
            score=result["score"],
            streak=result["streak"],
            multiplier=result["multiplier"],
            wordsCompleted=result["wordsCompleted"],
            confidence=round(confidence, 3),
            timeRemaining=result["timeRemaining"],
            isActive=result["isActive"],
            buffer_status=status,
        )

    ml_key = _ml_key(user_id, game.game_id)
    if not throttle.allow(ml_key):
        return respond(game.record_attempt(None), 0.0, "throttled")

    try:
        frame = decode_base64_frame(request.frame)
    except FrameDecodeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not validate_frame(frame):
        raise HTTPException(status_code=400, detail="Invalid frame")
    frame = resize_frame(frame, target_width=640)

    predicted, confidence, status, _, _ = predict_from_raw_frame(session_id=ml_key, frame=frame)

    with session.lock:
        if predicted is not None and not is_relevant_prediction(game.current_challenge, predicted):
            predicted = None  # letter predictions while performing a word sign don't count
        challenge_before = game.current_challenge
        result = game.record_attempt(predicted)
    if result["correct"] or (predicted is not None and predicted != challenge_before):
        reset_buffer(ml_key)  # each sign gets a fresh window

    return respond(result, confidence, status)


@router.get("/result/{session_id}/{game_id}", response_model=GameResultResponse)
def game_result(session_id: str, game_id: str, current_user: Dict = Depends(get_current_user)):
    """End the game (idempotent) and return final results."""
    require_own_session(current_user, session_id)

    session = get_session(session_id)
    game = session.get_game(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    session.finish_game(game_id)
    reset_session(_ml_key(session_id, game_id))
    throttle.forget(_ml_key(session_id, game_id))
    return GameResultResponse(**game.get_final_result())
