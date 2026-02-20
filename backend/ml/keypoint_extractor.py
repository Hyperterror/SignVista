"""
SignVista Keypoint Extractor

Extracts 33 Pose landmarks from a video frame using Mediapipe.
Produces a 99-dimensional feature vector (33 landmarks × 3 coords).

Ishit: If you're also using Mediapipe Hands (21 landmarks), extend this
       to concatenate both Pose + Hands features and update INPUT_SIZE.
"""

import logging

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Lazy-load mediapipe to avoid import errors in environments without it
_pose = None


def _get_pose():
    """Lazy-initialize Mediapipe Pose."""
    global _pose
    if _pose is None:
        try:
            import mediapipe as mp
            _pose = mp.solutions.pose.Pose(
                static_image_mode=False,
                model_complexity=1,       # 0=lite, 1=full, 2=heavy
                enable_segmentation=False,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            logger.info("✅ Mediapipe Pose initialized successfully")
        except ImportError:
            logger.warning("⚠️ Mediapipe not installed — keypoint extraction will use mock data")
            _pose = "unavailable"
        except Exception as e:
            logger.error(f"❌ Mediapipe Pose init failed: {e}")
            _pose = "unavailable"
    return _pose


def extract_keypoints(frame: np.ndarray) -> np.ndarray:
    """
    Extract 33 Pose landmarks from a BGR frame.

    Args:
        frame: BGR image array from OpenCV

    Returns:
        np.ndarray of shape (99,) — flattened [x1, y1, z1, x2, y2, z2, ...]
        Returns zeros if no pose detected.
    """
    pose = _get_pose()

    if pose == "unavailable":
        # Mock: return random keypoints for testing without Mediapipe
        return np.random.randn(99).astype(np.float32) * 0.1

    try:
        # Mediapipe expects RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(frame_rgb)

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            # Flatten: [x1, y1, z1, x2, y2, z2, ...] = 33 × 3 = 99
            keypoints = np.array([
                [lm.x, lm.y, lm.z] for lm in landmarks
            ]).flatten().astype(np.float32)
            return keypoints
        else:
            # No pose detected — return zeros
            logger.debug("No pose landmarks detected in frame")
            return np.zeros(99, dtype=np.float32)

    except Exception as e:
        logger.error(f"Keypoint extraction error: {e}")
        return np.zeros(99, dtype=np.float32)


def extract_hand_keypoints(frame: np.ndarray) -> np.ndarray:
    """
    Extract 21 Hand landmarks using Mediapipe Hands.
    Used for static alphabet recognition (Maitree ANN model).

    Ishit: Implement this if using Maitree's hand-based model.

    Args:
        frame: BGR image array

    Returns:
        np.ndarray of shape (63,) — 21 landmarks × 3 coords
        Returns zeros if no hand detected.
    """
    try:
        import mediapipe as mp
        mp_hands = mp.solutions.hands.Hands(
            static_image_mode=True,
            max_num_hands=2,
            min_detection_confidence=0.5,
        )

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = mp_hands.process(frame_rgb)

        if results.multi_hand_landmarks:
            hand = results.multi_hand_landmarks[0]
            keypoints = np.array([
                [lm.x, lm.y, lm.z] for lm in hand.landmark
            ]).flatten().astype(np.float32)
            mp_hands.close()
            return keypoints

        mp_hands.close()
        return np.zeros(63, dtype=np.float32)

    except Exception as e:
        logger.error(f"Hand keypoint extraction error: {e}")
        return np.zeros(63, dtype=np.float32)
