"""
SignVista — AR Landmarks Route

POST /api/ar/landmarks — Extract pose + hand landmarks for AR overlay rendering.

Unlike /api/recognize-frame which returns a predicted word, this endpoint
returns the raw landmark coordinates so Ayush can render AR overlays
(skeleton lines, hand outlines, gesture guides) on the camera feed.

Ayush: Send frames here when AR mode is active. Use the landmark coordinates
       to draw pose skeleton and hand outlines on the canvas overlay.
"""

import logging

import cv2
import numpy as np
from fastapi import APIRouter, HTTPException

from app.schemas import (
    ARLandmarksRequest,
    ARLandmarksResponse,
    LandmarkPoint,
)
from app.utils.frame_utils import decode_base64_frame, validate_frame, resize_frame, FrameDecodeError
from ml.face_detector import detect_face
from ml.inference import predict_from_raw_frame

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ar", tags=["AR"])


def _extract_landmarks_full(frame: np.ndarray) -> dict:
    """
    Extract both pose and hand landmarks from a frame.
    Returns all landmark data needed for AR overlay.
    """
    result = {
        "pose_landmarks": [],
        "left_hand_landmarks": [],
        "right_hand_landmarks": [],
        "face_detected": False,
    }

    # Face detection
    result["face_detected"] = detect_face(frame)

    # Extract pose landmarks via Mediapipe
    try:
        import mediapipe as mp

        # Pose landmarks (33 points)
        with mp.solutions.pose.Pose(
            static_image_mode=True,
            model_complexity=1,
            min_detection_confidence=0.5,
        ) as pose:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pose_results = pose.process(frame_rgb)

            if pose_results.pose_landmarks:
                for lm in pose_results.pose_landmarks.landmark:
                    result["pose_landmarks"].append(
                        LandmarkPoint(
                            x=round(lm.x, 4),
                            y=round(lm.y, 4),
                            z=round(lm.z, 4),
                            visibility=round(lm.visibility, 3),
                        )
                    )

        # Hand landmarks (21 points per hand)
        with mp.solutions.hands.Hands(
            static_image_mode=True,
            max_num_hands=2,
            min_detection_confidence=0.5,
        ) as hands:
            hand_results = hands.process(frame_rgb)

            if hand_results.multi_hand_landmarks:
                for idx, hand_lms in enumerate(hand_results.multi_hand_landmarks):
                    hand_points = []
                    for lm in hand_lms.landmark:
                        hand_points.append(
                            LandmarkPoint(
                                x=round(lm.x, 4),
                                y=round(lm.y, 4),
                                z=round(lm.z, 4),
                                visibility=1.0,
                            )
                        )

                    # Determine handedness
                    if hand_results.multi_handedness:
                        handedness = hand_results.multi_handedness[idx].classification[0].label
                        if handedness == "Left":
                            result["left_hand_landmarks"] = hand_points
                        else:
                            result["right_hand_landmarks"] = hand_points
                    else:
                        if idx == 0:
                            result["right_hand_landmarks"] = hand_points
                        else:
                            result["left_hand_landmarks"] = hand_points

    except ImportError:
        logger.warning("⚠️ Mediapipe not installed — returning mock AR landmarks")
        # Return mock pose landmarks for testing
        result["pose_landmarks"] = [
            LandmarkPoint(x=0.5, y=0.3 + i * 0.02, z=0.0, visibility=0.9)
            for i in range(33)
        ]
        result["right_hand_landmarks"] = [
            LandmarkPoint(x=0.6, y=0.5 + i * 0.01, z=0.0, visibility=0.9)
            for i in range(21)
        ]
    except Exception as e:
        logger.error(f"AR landmark extraction error: {e}")

    return result


@router.post("/landmarks", response_model=ARLandmarksResponse)
async def get_ar_landmarks(request: ARLandmarksRequest):
    """
    Extract pose and hand landmarks from a camera frame for AR overlay.

    Returns 33 pose landmarks + up to 21 landmarks per hand,
    plus any current sign prediction if the buffer is ready.

    Ayush uses these coordinates to draw:
    - Pose skeleton lines connecting body joints
    - Hand outlines with finger connections
    - Gesture hint overlays (e.g., "Move hand higher")

    Ayush sends:
    ```json
    {
        "sessionId": "user-123",
        "frame": "data:image/jpeg;base64,..."
    }
    ```

    Response includes all landmark coordinates as (x, y, z) normalized
    to the frame dimensions (0.0-1.0). Ayush multiplies by canvas
    width/height to get pixel positions.
    """
    if not request.sessionId or not request.sessionId.strip():
        raise HTTPException(status_code=400, detail="sessionId is required")

    # Decode frame
    try:
        frame = decode_base64_frame(request.frame)
    except FrameDecodeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not validate_frame(frame):
        raise HTTPException(status_code=400, detail="Invalid frame")

    frame = resize_frame(frame, target_width=640)

    # Extract landmarks
    landmarks = _extract_landmarks_full(frame)

    # Also run prediction pipeline (piggyback on the same frame)
    predicted, confidence, buffer_status = predict_from_raw_frame(
        session_id=request.sessionId,
        frame=frame,
    )

    # Generate gesture hint based on landmark analysis
    gesture_hint = ""
    if not landmarks["face_detected"]:
        gesture_hint = "Please show your face to the camera"
    elif not landmarks["right_hand_landmarks"] and not landmarks["left_hand_landmarks"]:
        gesture_hint = "Raise your hands to start signing"
    elif predicted and confidence > 0.5:
        gesture_hint = f"Detected: {predicted} ({confidence:.0%})"

    return ARLandmarksResponse(
        pose_landmarks=landmarks["pose_landmarks"],
        left_hand_landmarks=landmarks["left_hand_landmarks"],
        right_hand_landmarks=landmarks["right_hand_landmarks"],
        face_detected=landmarks["face_detected"],
        prediction=predicted,
        confidence=round(confidence, 3),
        gesture_hint=gesture_hint,
    )
