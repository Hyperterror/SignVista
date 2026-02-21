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

    # Run ML inference pipeline + get raw landmarks (one pass!)
    predicted, confidence, status, results, module_details = predict_from_raw_frame(
        session_id=request.sessionId,
        frame=frame,
        return_landmarks=True,
        return_module_details=True
    )
    
    # Log prediction for debugging
    if predicted:
        logger.info(f"AR Prediction: {predicted} (confidence: {confidence:.3f})")
    if module_details:
        logger.info(f"Module details: {module_details}")

    # Transform Mediapipe results to AR response format
    pose_lms = []
    lh_lms = []
    rh_lms = []
    
    if results:
        if results.pose_landmarks:
            pose_lms = [
                LandmarkPoint(x=round(lm.x, 4), y=round(lm.y, 4), z=round(lm.z, 4), visibility=round(lm.visibility, 3))
                for lm in results.pose_landmarks.landmark
            ]
        if results.left_hand_landmarks:
            lh_lms = [
                LandmarkPoint(x=round(lm.x, 4), y=round(lm.y, 4), z=round(lm.z, 4), visibility=1.0)
                for lm in results.left_hand_landmarks.landmark
            ]
        if results.right_hand_landmarks:
            rh_lms = [
                LandmarkPoint(x=round(lm.x, 4), y=round(lm.y, 4), z=round(lm.z, 4), visibility=1.0)
                for lm in results.right_hand_landmarks.landmark
            ]

    # Face detection using existing utility
    from ml.face_detector import detect_face
    face_detected = detect_face(frame)

    # Generate gesture hint
    gesture_hint = ""
    if not face_detected:
        gesture_hint = "Please show your face"
    elif not lh_lms and not rh_lms:
        gesture_hint = "Raise your hands to start"
    elif predicted and confidence > settings.CONFIDENCE_THRESHOLD:
        gesture_hint = f"Detected: {predicted}"
    elif "collecting" in status:
        gesture_hint = f"Analyzing... {status.split('_')[-1]}"

    return ARLandmarksResponse(
        pose_landmarks=pose_lms,
        left_hand_landmarks=lh_lms,
        right_hand_landmarks=rh_lms,
        face_detected=face_detected,
        prediction=predicted,
        confidence=round(confidence, 3),
        gesture_hint=gesture_hint,
    )
