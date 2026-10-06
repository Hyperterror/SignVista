"""
SignVista Keypoint Extractor

Extracts landmarks once per frame and shares them with every module.

Uses the MediaPipe Tasks API (PoseLandmarker + HandLandmarker) — the legacy
`mp.solutions.holistic` API no longer exists in current MediaPipe releases.

Recognition feature vector (258 values, same layout as legacy Holistic):
- Pose: 33 landmarks × 4 (x, y, z, visibility) = 132
- Left hand (subject's left): 21 × 3 (x, y, z) = 63
- Right hand (subject's right): 21 × 3 (x, y, z) = 63

Hands are assigned to the subject's left/right by matching each hand's wrist
to the pose wrists — the same way Holistic derives its hand ROIs. If no pose
is visible we fall back to the HandLandmarker label, swapped because frames
from the browser are not mirrored.

Landmarkers run in IMAGE mode (stateless), so one instance can serve any
session; a small pool lets several requests run concurrently.
"""

import logging
import os
import queue
import threading
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import cv2
import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)

KEYPOINT_DIM = 258
POSE_LEFT_WRIST = 15
POSE_RIGHT_WRIST = 16

POSE_MODEL_FILE = "pose_landmarker_full.task"
HAND_MODEL_FILE = "hand_landmarker.task"

# (x, y, z, visibility)
Point = Tuple[float, float, float, float]


@dataclass
class FrameLandmarks:
    """Landmarks extracted from one frame (coordinates normalized to [0, 1])."""
    pose: List[Point] = field(default_factory=list)
    left_hand: List[Point] = field(default_factory=list)   # subject's left hand
    right_hand: List[Point] = field(default_factory=list)  # subject's right hand
    hands: List[List[Point]] = field(default_factory=list)  # all hands, detector order
    image_width: int = 0
    image_height: int = 0

    @property
    def has_hands(self) -> bool:
        return bool(self.hands)

    def to_keypoints(self) -> np.ndarray:
        pose = np.array(self.pose, dtype=np.float32).flatten() if self.pose else np.zeros(132, dtype=np.float32)
        lh = np.array([p[:3] for p in self.left_hand], dtype=np.float32).flatten() if self.left_hand else np.zeros(63, dtype=np.float32)
        rh = np.array([p[:3] for p in self.right_hand], dtype=np.float32).flatten() if self.right_hand else np.zeros(63, dtype=np.float32)
        return np.concatenate([pose, lh, rh]).astype(np.float32)


class _Landmarkers:
    """One PoseLandmarker + HandLandmarker pair (not thread-safe; pooled)."""

    def __init__(self, mp, models_dir: str):
        vision = mp.tasks.vision
        base = mp.tasks.BaseOptions
        self.pose = vision.PoseLandmarker.create_from_options(vision.PoseLandmarkerOptions(
            base_options=base(model_asset_path=os.path.join(models_dir, POSE_MODEL_FILE)),
            running_mode=vision.RunningMode.IMAGE,
            num_poses=1,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
        ))
        self.hands = vision.HandLandmarker.create_from_options(vision.HandLandmarkerOptions(
            base_options=base(model_asset_path=os.path.join(models_dir, HAND_MODEL_FILE)),
            running_mode=vision.RunningMode.IMAGE,
            num_hands=2,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
        ))

    def close(self):
        for lm in (self.pose, self.hands):
            try:
                lm.close()
            except Exception:
                pass


class _LandmarkerPool:
    def __init__(self, size: int):
        self._size = size
        self._pool: "queue.Queue[_Landmarkers]" = queue.Queue()
        self._created = 0
        self._lock = threading.Lock()
        self._mp = None
        self.available: Optional[bool] = None

    def _init_mp(self) -> bool:
        if self.available is not None:
            return self.available
        try:
            import mediapipe as mp
            models_dir = settings.MEDIAPIPE_MODELS_DIR
            missing = [f for f in (POSE_MODEL_FILE, HAND_MODEL_FILE)
                       if not os.path.exists(os.path.join(models_dir, f))]
            if missing:
                logger.error(f"❌ MediaPipe model files missing in {models_dir}: {missing}")
                self.available = False
            else:
                self._mp = mp
                self.available = True
        except ImportError:
            logger.warning("⚠️ MediaPipe not installed — keypoint extraction disabled")
            self.available = False
        return self.available

    def acquire(self) -> Optional[_Landmarkers]:
        with self._lock:
            if not self._init_mp():
                return None
            try:
                return self._pool.get_nowait()
            except queue.Empty:
                if self._created < self._size:
                    try:
                        inst = _Landmarkers(self._mp, settings.MEDIAPIPE_MODELS_DIR)
                    except Exception as e:
                        logger.error(f"❌ Failed to create MediaPipe landmarkers: {e}")
                        self.available = False
                        return None
                    self._created += 1
                    if self._created == 1:
                        logger.info("✅ MediaPipe Pose + Hand landmarkers initialized")
                    return inst
        # Pool exhausted: wait for a free instance
        return self._pool.get()

    def release(self, inst: _Landmarkers) -> None:
        self._pool.put(inst)

    @property
    def mp(self):
        return self._mp


_pool = _LandmarkerPool(size=max(1, min(4, (os.cpu_count() or 2) // 2)))


def _to_points(landmarks, with_visibility: bool) -> List[Point]:
    pts = []
    for lm in landmarks:
        vis = getattr(lm, "visibility", None) if with_visibility else 1.0
        pts.append((float(lm.x), float(lm.y), float(lm.z), float(vis if vis is not None else 0.0)))
    return pts


def _assign_hands(pose: List[Point], hands: List[List[Point]], labels: List[str]) -> Tuple[List[Point], List[Point]]:
    """Return (subject_left, subject_right) hand landmarks."""
    left: List[Point] = []
    right: List[Point] = []
    if pose and len(pose) > POSE_RIGHT_WRIST:
        lw, rw = pose[POSE_LEFT_WRIST], pose[POSE_RIGHT_WRIST]
        for hand in hands:
            wx, wy = hand[0][0], hand[0][1]
            d_left = (wx - lw[0]) ** 2 + (wy - lw[1]) ** 2
            d_right = (wx - rw[0]) ** 2 + (wy - rw[1]) ** 2
            if d_left <= d_right and not left:
                left = hand
            elif not right:
                right = hand
            elif not left:
                left = hand
        return left, right

    # No pose: HandLandmarker labels assume a mirrored image; browser frames aren't mirrored
    for hand, label in zip(hands, labels, strict=False):
        if label == "Right" and not left:
            left = hand
        elif label == "Left" and not right:
            right = hand
    return left, right


def extract_landmarks(frame: np.ndarray) -> Optional[FrameLandmarks]:
    """Run pose + hand landmarking on a BGR frame. Returns None if unavailable."""
    inst = _pool.acquire()
    if inst is None:
        return None
    try:
        mp = _pool.mp
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb))

        pose_result = inst.pose.detect(image)
        hand_result = inst.hands.detect(image)

        pose = _to_points(pose_result.pose_landmarks[0], True) if pose_result.pose_landmarks else []
        hands = [_to_points(h, False) for h in (hand_result.hand_landmarks or [])]
        labels = [h[0].category_name for h in (hand_result.handedness or [])]
        left, right = _assign_hands(pose, hands, labels)

        return FrameLandmarks(
            pose=pose, left_hand=left, right_hand=right, hands=hands,
            image_width=frame.shape[1], image_height=frame.shape[0],
        )
    except Exception as e:
        logger.error(f"Landmark extraction error: {e}", exc_info=True)
        return None
    finally:
        _pool.release(inst)


def extract_keypoints(frame: np.ndarray, return_results: bool = False) -> Tuple[np.ndarray, Optional[FrameLandmarks]]:
    """
    Extract the 258-feature recognition vector [Pose(132), LH(63), RH(63)].

    Returns zeros when extraction is unavailable. `results` is the
    FrameLandmarks object when return_results=True.
    """
    landmarks = extract_landmarks(frame)
    if landmarks is None:
        return np.zeros(KEYPOINT_DIM, dtype=np.float32), None
    return landmarks.to_keypoints(), (landmarks if return_results else None)


def is_available() -> bool:
    inst = _pool.acquire()
    if inst is None:
        return False
    _pool.release(inst)
    return True
