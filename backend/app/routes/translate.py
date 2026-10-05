"""
SignVista — Translate Route

POST /api/recognize-frame
Real-time ISL word recognition from webcam frames.

Ayush: Send a base64 JPEG frame every 200ms.
       Response includes word, confidence, buffer status, and history.
"""

import json
import logging

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.concurrency import run_in_threadpool

from app.schemas import RecognizeFrameRequest, RecognizeFrameResponse
from app.session_store import get_session
from app.utils.frame_utils import decode_base64_frame, validate_frame, resize_frame, FrameDecodeError
from ml.inference import predict_from_raw_frame

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Translate"])



@router.post("/recognize-frame", response_model=RecognizeFrameResponse)
def recognize_frame(
    request: RecognizeFrameRequest,
    return_module_details: bool = False
):
    """
    Process a single camera frame and return the predicted ISL word.

    Flow:
    1. Decode base64 → image
    2. Face detection gate
    3. Keypoint extraction (Mediapipe)
    4. Buffer 45 frames
    5. LSTM prediction
    6. Return word + confidence

    Args:
        request: Frame data with sessionId and base64 frame
        return_module_details: Optional query parameter to include detailed module information
                               in the response (active modules, all predictions, timing info)

    Ayush sends:
    ```json
    {
        "sessionId": "user-123",
        "frame": "data:image/jpeg;base64,/9j/4AAQ..."
    }
    ```
    """
    # Validate session ID
    if not request.sessionId or not request.sessionId.strip():
        raise HTTPException(status_code=400, detail="sessionId is required")

    # Decode frame
    try:
        frame = decode_base64_frame(request.frame)
    except FrameDecodeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Validate frame
    if not validate_frame(frame):
        raise HTTPException(status_code=400, detail="Invalid frame: too small or wrong format")

    # Resize for performance
    frame = resize_frame(frame, target_width=640)

    # Run ML inference pipeline (with landmarks for AR mapping if needed)
    word, confidence, buffer_status, _, module_details = predict_from_raw_frame(
        session_id=request.sessionId,
        frame=frame,
        return_module_details=return_module_details
    )

    # Rank predictions by confidence in descending order if module_details present
    if module_details and "predictions" in module_details:
        module_details["predictions"] = sorted(
            module_details["predictions"],
            key=lambda p: p["confidence"],
            reverse=True
        )

    # Update session history
    session = get_session(request.sessionId)
    if word is not None:
        session.translate.add_prediction(word, confidence)

    return RecognizeFrameResponse(
        word=word,
        confidence=round(confidence, 3),
        buffer_status=buffer_status,
        history=session.translate.get_history(),
        module_details=module_details
    )

@router.websocket("/ws/recognize")
async def websocket_recognize(websocket: WebSocket, session_id: str):
    """
    Real-time persistent connection for streaming frames without HTTP overhead.
    """
    await websocket.accept()
    session = get_session(session_id)
    
    try:
        while True:
            # Client sends the base64 payload as text
            data = await websocket.receive_text()
            
            try:
                # We expect the client to send a raw base64 string or JSON with a frame prop
                try:
                    payload = json.loads(data)
                    frame_data = payload.get("frame", "")
                    req_module_details = payload.get("module_details", False)
                except json.JSONDecodeError:
                    frame_data = data
                    req_module_details = False
                    
                frame = decode_base64_frame(frame_data)
            except FrameDecodeError as e:
                await websocket.send_json({"error": str(e)})
                continue

            if not validate_frame(frame):
                await websocket.send_json({"error": "Invalid frame"})
                continue

            frame = resize_frame(frame, target_width=640)

            # Avoid blocking the WebSocket async event loop with heavy ML inference
            word, confidence, buffer_status, _, module_details = await run_in_threadpool(
                predict_from_raw_frame,
                session_id=session_id,
                frame=frame,
                return_module_details=req_module_details
            )

            if word is not None:
                session.translate.add_prediction(word, confidence)

            resp = {
                "word": word,
                "confidence": round(confidence, 3),
                "buffer_status": buffer_status,
                "history": session.translate.get_history()
            }
            if req_module_details and module_details is not None:
                resp.update(module_details)

            await websocket.send_json(resp)
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.close()
        except:
            pass
