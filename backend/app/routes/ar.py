"""
SignVista — AR Landmarks Route

POST /api/ar/landmarks — pose + hand landmarks (plus current prediction) for
drawing the AR overlay. The WebSocket `/api/ws/recognize` with `"ar": true`
returns the same fields and is preferred for live video.
"""

import logging
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_current_user, require_own_session
from app.schemas import ARLandmarksRequest, ARLandmarksResponse
from app.utils.frame_pipeline import ar_payload, throttle
from app.utils.frame_utils import FrameDecodeError, decode_base64_frame, resize_frame, validate_frame
from ml.inference import predict_from_raw_frame

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ar", tags=["AR"])


@router.post("/landmarks", response_model=ARLandmarksResponse)
def get_ar_landmarks(request: ARLandmarksRequest, current_user: Dict = Depends(get_current_user)):
    """Extract pose and hand landmarks from a camera frame for the AR overlay."""
    if request.sessionId:
        require_own_session(current_user, request.sessionId)
    ml_key = f"{current_user['user_id']}:ar"

    if not throttle.allow(ml_key):
        return ARLandmarksResponse(gesture_hint="")

    try:
        frame = decode_base64_frame(request.frame)
    except FrameDecodeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not validate_frame(frame):
        raise HTTPException(status_code=400, detail="Invalid frame")
    frame = resize_frame(frame, target_width=640)

    predicted, confidence, status, landmarks, _ = predict_from_raw_frame(
        session_id=ml_key,
        frame=frame,
        return_landmarks=True,
    )
    return ARLandmarksResponse(**ar_payload(landmarks, predicted, confidence, status))
