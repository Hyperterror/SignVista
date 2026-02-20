"""
SignVista Face Detector

Uses OpenCV's Haar Cascade to detect faces as a prerequisite gate.
Inspired by AbhishekSinghDhadwal's face activation approach:
skip inference if no face is present (reduces false positives).

Ishit: If you integrate YOLO or a better detector, replace this module.
"""

import logging

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Lazy-load cascade classifier
_face_cascade = None


def _get_cascade():
    """Lazy-initialize Haar cascade face detector."""
    global _face_cascade
    if _face_cascade is None:
        try:
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            _face_cascade = cv2.CascadeClassifier(cascade_path)
            if _face_cascade.empty():
                logger.warning("⚠️ Haar cascade file not found — face detection disabled")
                _face_cascade = "unavailable"
            else:
                logger.info("✅ Haar cascade face detector loaded")
        except Exception as e:
            logger.error(f"❌ Face cascade init failed: {e}")
            _face_cascade = "unavailable"
    return _face_cascade


def detect_face(frame: np.ndarray) -> bool:
    """
    Check if at least one face is present in the frame.

    This is used as a gate for inference — if no face is visible,
    the person is likely not signing and we skip prediction.

    Args:
        frame: BGR image array

    Returns:
        True if face detected, False otherwise.
        Returns True if detector is unavailable (permissive fallback).
    """
    cascade = _get_cascade()

    if cascade == "unavailable":
        # If detector isn't available, don't block inference
        return True

    try:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(80, 80),
            flags=cv2.CASCADE_SCALE_IMAGE,
        )

        has_face = len(faces) > 0
        if not has_face:
            logger.debug("No face detected — skipping inference")
        return has_face

    except Exception as e:
        logger.error(f"Face detection error: {e}")
        return True  # Permissive fallback
