"""
Shared frame-processing helpers for HTTP and WebSocket routes:
- per-session frame-rate throttling (protects the CPU-heavy ML pipeline)
- AR overlay payload construction
"""

import threading
import time
from typing import Dict, List, Optional

from app.config import settings
from ml.keypoint_extractor import FrameLandmarks

POSE_NOSE = 0
POSE_EYES = (2, 5)


class FrameThrottle:
    """Drops frames that arrive faster than FRAME_PROCESS_FPS for a given key."""

    def __init__(self):
        self._last: Dict[str, float] = {}
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        fps = settings.FRAME_PROCESS_FPS
        if fps <= 0:
            return True
        min_interval = 1.0 / fps
        now = time.monotonic()
        with self._lock:
            last = self._last.get(key, 0.0)
            if now - last < min_interval * 0.9:  # small tolerance for network jitter
                return False
            self._last[key] = now
            if len(self._last) > 10_000:
                cutoff = now - 600
                self._last = {k: v for k, v in self._last.items() if v >= cutoff}
            return True

    def forget(self, key: str) -> None:
        with self._lock:
            self._last.pop(key, None)


throttle = FrameThrottle()


def _points(points) -> List[Dict[str, float]]:
    return [
        {"x": round(p[0], 4), "y": round(p[1], 4), "z": round(p[2], 4), "visibility": round(p[3], 3)}
        for p in points
    ]


def face_visible(landmarks: Optional[FrameLandmarks]) -> bool:
    """Face is considered visible when the pose nose/eyes are confidently detected."""
    if landmarks is None or not landmarks.pose:
        return False
    idx = (POSE_NOSE, *POSE_EYES)
    return max(landmarks.pose[i][3] for i in idx) >= 0.5


def gesture_hint(status: str, predicted: Optional[str], confidence: float, landmarks: Optional[FrameLandmarks]) -> str:
    if status == "no_model":
        return "Sign recognition model is unavailable"
    if status == "throttled":
        return ""
    if landmarks is not None and not landmarks.pose:
        return "Step into the frame so your upper body is visible"
    if landmarks is not None and not landmarks.has_hands:
        return "Raise your hands to start"
    if predicted and confidence >= settings.CONFIDENCE_THRESHOLD:
        return f"Detected: {predicted}"
    if status.startswith("collecting"):
        return f"Analyzing... {status.split('_')[-1]}"
    return "Listening for signs..."


def ar_payload(landmarks: Optional[FrameLandmarks], predicted: Optional[str], confidence: float, status: str) -> Dict:
    """Landmark coordinates + hints for drawing the AR overlay."""
    return {
        "pose_landmarks": _points(landmarks.pose) if landmarks else [],
        "left_hand_landmarks": _points(landmarks.left_hand) if landmarks else [],
        "right_hand_landmarks": _points(landmarks.right_hand) if landmarks else [],
        "face_detected": face_visible(landmarks),
        "prediction": predicted,
        "confidence": round(confidence, 3),
        "gesture_hint": gesture_hint(status, predicted, confidence, landmarks),
    }
