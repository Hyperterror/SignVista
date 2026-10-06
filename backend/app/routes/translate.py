"""
SignVista — Translate Routes

POST /api/recognize-frame   — recognize one camera frame (authenticated)
WS   /api/ws/recognize      — stream frames over a persistent connection

WebSocket protocol:
- connect with `?ticket=<ticket from POST /api/auth/ws-ticket>`
- send JSON `{"frame": "<base64 jpeg>", "module_details": bool, "ar": bool}`
- every message gets exactly one JSON reply, so the client should send the
  next frame only after receiving the previous reply (natural backpressure)
"""

import json
import logging
import uuid
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.concurrency import run_in_threadpool

from app.dependencies import authenticate_websocket, get_current_user, require_own_session
from app.schemas import RecognizeFrameRequest, RecognizeFrameResponse
from app.session_store import get_session
from app.utils.frame_pipeline import ar_payload, throttle
from app.utils.frame_utils import FrameDecodeError, decode_base64_frame, resize_frame, validate_frame
from ml.inference import predict_from_raw_frame, reset_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Translate"])

WS_POLICY_VIOLATION = 1008
MAX_WS_MESSAGE_CHARS = 2 * 1024 * 1024


@router.post("/recognize-frame", response_model=RecognizeFrameResponse)
def recognize_frame(
    request: RecognizeFrameRequest,
    return_module_details: bool = False,
    current_user: Dict = Depends(get_current_user),
):
    """Process a single camera frame and return the predicted ISL sign."""
    session_id = current_user["user_id"]
    if request.sessionId:
        require_own_session(current_user, request.sessionId)

    session = get_session(session_id)
    if not throttle.allow(f"translate:{session_id}"):
        return RecognizeFrameResponse(word=None, confidence=0.0, buffer_status="throttled",
                                      history=session.translate.get_history())

    try:
        frame = decode_base64_frame(request.frame)
    except FrameDecodeError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if not validate_frame(frame):
        raise HTTPException(status_code=400, detail="Invalid frame: too small or wrong format")
    frame = resize_frame(frame, target_width=640)

    word, confidence, buffer_status, _, module_details = predict_from_raw_frame(
        session_id=session_id,
        frame=frame,
        return_module_details=return_module_details,
    )
    if module_details and module_details.get("predictions"):
        module_details["predictions"].sort(key=lambda p: p["confidence"], reverse=True)

    if word is not None:
        session.translate.add_prediction(word, confidence)

    return RecognizeFrameResponse(
        word=word,
        confidence=round(confidence, 3),
        buffer_status=buffer_status,
        history=session.translate.get_history(),
        module_details=module_details,
    )


def _process_ws_frame(session_id: str, ml_key: str, data: str) -> Dict:
    """Blocking per-frame work for the WebSocket (runs in the threadpool)."""
    if len(data) > MAX_WS_MESSAGE_CHARS:
        return {"error": "Frame too large"}
    try:
        payload = json.loads(data)
        if not isinstance(payload, dict):
            raise ValueError
        frame_data = payload.get("frame", "")
        want_details = bool(payload.get("module_details", False))
        want_ar = bool(payload.get("ar", False))
    except (json.JSONDecodeError, ValueError):
        frame_data, want_details, want_ar = data, False, False

    session = get_session(session_id)
    if not throttle.allow(ml_key):
        return {"word": None, "confidence": 0.0, "buffer_status": "throttled",
                "history": session.translate.get_history()}

    try:
        frame = decode_base64_frame(frame_data)
    except FrameDecodeError as e:
        return {"error": str(e)}
    if not validate_frame(frame):
        return {"error": "Invalid frame"}
    frame = resize_frame(frame, target_width=640)

    word, confidence, status, landmarks, module_details = predict_from_raw_frame(
        session_id=ml_key,
        frame=frame,
        return_landmarks=want_ar,
        return_module_details=want_details,
    )
    if word is not None:
        session.translate.add_prediction(word, confidence)

    resp = {
        "word": word,
        "confidence": round(confidence, 3),
        "buffer_status": status,
        "history": session.translate.get_history(),
    }
    if want_details and module_details is not None:
        resp["module_details"] = module_details
    if want_ar:
        resp.update(ar_payload(landmarks, word, confidence, status))
    return resp


@router.websocket("/ws/recognize")
async def websocket_recognize(websocket: WebSocket):
    """Authenticated real-time recognition stream."""
    user = await run_in_threadpool(authenticate_websocket, websocket)
    if user is None:
        await websocket.close(code=WS_POLICY_VIOLATION)
        return

    session_id = user["user_id"]
    # Each connection gets its own ML buffers so two open tabs don't mix frames
    ml_key = f"{session_id}:ws:{uuid.uuid4().hex[:8]}"
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            try:
                resp = await run_in_threadpool(_process_ws_frame, session_id, ml_key, data)
            except Exception:
                logger.exception(f"Frame processing failed for {session_id}")
                resp = {"error": "Frame processing failed"}
            await websocket.send_json(resp)
    except WebSocketDisconnect:
        logger.info(f"Recognition WebSocket disconnected for {session_id}")
    except Exception:
        logger.exception(f"Recognition WebSocket error for {session_id}")
        try:
            await websocket.close()
        except Exception:
            pass
    finally:
        reset_session(ml_key)
        throttle.forget(ml_key)
