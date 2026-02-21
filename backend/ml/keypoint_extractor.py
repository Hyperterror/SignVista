"""
SignVista Keypoint Extractor

Extracts 258 features from a video frame using Mediapipe Holistic:
- Pose: 33 landmarks × 4 (x, y, z, visibility) = 132
- Left Hand: 21 landmarks × 3 (x, y, z) = 63
- Right Hand: 21 landmarks × 3 (x, y, z) = 63
- Total: 258 features
"""

import logging
import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Lazy-load Mediapipe
_holistic = None

def _get_holistic():
    """Lazy-initialize Mediapipe Holistic."""
    global _holistic
    if _holistic is None:
        try:
            import mediapipe as mp
            _holistic = mp.solutions.holistic.Holistic(
                static_image_mode=False,
                model_complexity=1,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            logger.info("✅ Mediapipe Holistic initialized")
        except ImportError:
            logger.warning("⚠️ Mediapipe not installed")
            _holistic = "unavailable"
    return _holistic

def extract_keypoints(frame: np.ndarray, return_results: bool = False) -> tuple[np.ndarray, any]:
    """
    Extract 258 features [Pose(132), LH(63), RH(63)].
    """
    holistic = _get_holistic()
    if holistic == "unavailable":
        return np.zeros(258, dtype=np.float32), None

    try:
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = holistic.process(frame_rgb)

        # 1. Pose (33 * 4 = 132)
        pose = np.array([[res.x, res.y, res.z, res.visibility] for res in results.pose_landmarks.landmark]).flatten() if results.pose_landmarks else np.zeros(132)
        
        # 2. Left Hand (21 * 3 = 63)
        lh = np.array([[res.x, res.y, res.z] for res in results.left_hand_landmarks.landmark]).flatten() if results.left_hand_landmarks else np.zeros(63)
        
        # 3. Right Hand (21 * 3 = 63)
        rh = np.array([[res.x, res.y, res.z] for res in results.right_hand_landmarks.landmark]).flatten() if results.right_hand_landmarks else np.zeros(63)

        keypoints = np.concatenate([pose, lh, rh]).astype(np.float32)
        return keypoints, (results if return_results else None)

    except Exception as e:
        logger.error(f"Holistic extraction error: {e}")
        return np.zeros(258, dtype=np.float32), None
