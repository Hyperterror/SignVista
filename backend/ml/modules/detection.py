"""
Detection Module for ISL Unified Models Integration.

MediaPipe hand landmarks + FNN classifier for static gestures (1-9, A-Z) — 35 classes.

Preprocessing matches how the classifier was trained
(ISL-Unified-Project/detection/isl_detection.py):
- the frame is mirrored horizontally (training used cv2.flip(image, 1))
- landmarks are converted to integer pixel coordinates
- coordinates are made relative to the wrist and normalized by the max absolute value

Temporal smoothing (prediction must repeat on consecutive frames) is tracked
per session, so users never influence each other's results.
"""

import logging
import threading
import time
from collections import OrderedDict
from typing import Any, Dict, List, Optional

import numpy as np

from ..keypoint_extractor import FrameLandmarks, extract_landmarks
from ..vocabulary import get_display_name, get_word_by_module_index
from . import ModulePrediction

logger = logging.getLogger(__name__)

MAX_TRACKED_SESSIONS = 1000


class DetectionModule:
    """Static gesture recognition (letters and digits) from a single frame."""

    def __init__(self, model: Any, config: Dict[str, Any]):
        """
        Args:
            model: Loaded FNN gesture classifier (Keras model)
            config: {"confidence_threshold": float, "preprocessing_params": {...}}
        """
        self.model = model
        self.config = config
        self.confidence_threshold = config.get("confidence_threshold", 0.7)

        params = config.get("preprocessing_params", {}) or {}
        self.min_margin = params.get("min_confidence_margin", 0.15)
        self.history_size = params.get("smoothing_window", 2)

        self._history: "OrderedDict[str, List[str]]" = OrderedDict()
        self._history_lock = threading.Lock()
        self._model_lock = threading.Lock()

        logger.info(
            f"✅ Detection module initialized (threshold={self.confidence_threshold}, "
            f"margin={self.min_margin}, smoothing={self.history_size})"
        )

    # ── Smoothing state ──────────────────────────────────────────

    def _consistent(self, session_id: str, word: str) -> bool:
        """Record a prediction and return True once it repeats over the smoothing window."""
        if self.history_size <= 1:
            return True
        with self._history_lock:
            hist = self._history.pop(session_id, [])
            hist = (hist + [word])[-self.history_size:]
            self._history[session_id] = hist
            while len(self._history) > MAX_TRACKED_SESSIONS:
                self._history.popitem(last=False)
            return len(hist) == self.history_size and len(set(hist)) == 1

    def reset_session(self, session_id: str) -> None:
        with self._history_lock:
            self._history.pop(session_id, None)

    # ── Preprocessing ────────────────────────────────────────────

    @staticmethod
    def hand_to_features(hand: List, image_width: int, image_height: int) -> np.ndarray:
        """
        21 normalized landmarks of one hand -> (42,) pixel coordinates of the
        horizontally mirrored frame (the training convention).
        """
        feats = []
        for p in hand:
            x = min(int((1.0 - p[0]) * image_width), image_width - 1)
            y = min(int(p[1] * image_height), image_height - 1)
            feats.extend((x, y))
        return np.array(feats, dtype=np.float32)

    def extract_hand_landmarks(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """Features (42,) for the first detected hand, or None if no hands."""
        lm = extract_landmarks(frame)
        if lm is None or not lm.hands:
            return None
        return self.hand_to_features(lm.hands[0], lm.image_width, lm.image_height)

    def preprocess_landmarks(self, landmarks: np.ndarray) -> np.ndarray:
        """Relative-to-wrist coordinates normalized by max |value|, shaped (1, 42)."""
        processed = landmarks.astype(np.float32).copy()
        processed[0::2] -= processed[0]
        processed[1::2] -= processed[1]
        max_val = np.max(np.abs(processed))
        if max_val > 0:
            processed = processed / max_val
        return processed.reshape(1, -1)

    # ── Inference ────────────────────────────────────────────────

    def predict(
        self,
        frame: Optional[np.ndarray] = None,
        session_id: str = "default",
        landmarks: Optional[FrameLandmarks] = None,
    ) -> Optional[ModulePrediction]:
        """
        Classify the gesture of the most confidently recognized hand.

        Returns None if no hands, low confidence, ambiguous, or not yet stable.
        """
        start_time = time.time()
        try:
            if landmarks is None:
                if frame is None:
                    return None
                landmarks = extract_landmarks(frame)
            if landmarks is None or not landmarks.hands:
                return None

            batch = np.vstack([
                self.preprocess_landmarks(
                    self.hand_to_features(hand, landmarks.image_width, landmarks.image_height)
                )
                for hand in landmarks.hands
            ])
            preprocessing_time = time.time() - start_time

            inference_start = time.time()
            with self._model_lock:
                probs = np.asarray(self.model.predict(batch, verbose=0))
            inference_time = time.time() - inference_start

            # Pick the hand whose top prediction is most confident
            best_hand = int(np.argmax(probs.max(axis=1)))
            row = probs[best_hand]
            order = np.argsort(row)[::-1]
            class_index = int(order[0])
            confidence = float(row[class_index])
            second = float(row[order[1]]) if len(order) > 1 else 0.0
            word = get_word_by_module_index("detection", class_index)
            display_name = get_display_name(word, "detection")

            if confidence - second < self.min_margin:
                logger.debug(f"Detection: {display_name} ambiguous (margin={confidence - second:.3f})")
                return None
            if confidence < self.confidence_threshold:
                logger.debug(f"Detection: {display_name} {confidence:.3f} below threshold {self.confidence_threshold}")
                return None
            if not self._consistent(session_id, word):
                return None

            return ModulePrediction(
                module_name="detection",
                class_index=class_index,
                word=word,
                display_name=display_name,
                confidence=confidence,
                preprocessing_time=preprocessing_time,
                inference_time=inference_time,
                metadata={"num_hands": len(landmarks.hands), "confidence_margin": confidence - second},
                timestamp=time.time(),
            )
        except Exception as e:
            logger.error(f"Detection module prediction failed: {e}", exc_info=True)
            return None
