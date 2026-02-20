"""
SignVista Frame Utilities

Handles base64 frame decoding and validation.
Used by all routes that receive camera frames.
"""

import base64
import re

import cv2
import numpy as np

from app.config import settings


class FrameDecodeError(Exception):
    """Raised when frame decoding fails."""
    pass


def decode_base64_frame(frame_str: str) -> np.ndarray:
    """
    Decode a base64-encoded JPEG frame into an OpenCV-compatible numpy array.

    Accepts both:
    - Raw base64: "/9j/4AAQSkZJRg..."
    - Data URI:   "data:image/jpeg;base64,/9j/4AAQSkZJRg..."

    Args:
        frame_str: Base64-encoded frame string

    Returns:
        np.ndarray: BGR image array (OpenCV format)

    Raises:
        FrameDecodeError: If decoding or validation fails
    """
    if not frame_str:
        raise FrameDecodeError("Frame data is empty")

    # Strip data URI prefix if present
    if frame_str.startswith("data:"):
        match = re.match(r"data:image/\w+;base64,(.+)", frame_str)
        if not match:
            raise FrameDecodeError("Invalid data URI format")
        frame_str = match.group(1)

    # Validate size (base64 is ~33% larger than raw bytes)
    estimated_bytes = len(frame_str) * 3 / 4
    if estimated_bytes > settings.MAX_FRAME_SIZE_BYTES:
        raise FrameDecodeError(
            f"Frame too large: ~{estimated_bytes / 1024:.0f}KB "
            f"(max {settings.MAX_FRAME_SIZE_BYTES / 1024:.0f}KB)"
        )

    try:
        # Decode base64 to bytes
        img_bytes = base64.b64decode(frame_str)
    except Exception as e:
        raise FrameDecodeError(f"Base64 decode failed: {str(e)}")

    # Convert to numpy array
    nparr = np.frombuffer(img_bytes, np.uint8)

    # Decode image
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if frame is None:
        raise FrameDecodeError("Failed to decode image — invalid JPEG data")

    return frame


def validate_frame(frame: np.ndarray) -> bool:
    """
    Validate that a decoded frame is usable.

    Args:
        frame: Decoded BGR image array

    Returns:
        True if frame is valid
    """
    if frame is None:
        return False
    if len(frame.shape) != 3:
        return False
    h, w, c = frame.shape
    if h < 100 or w < 100:  # Too small
        return False
    if c != 3:  # Must be BGR
        return False
    return True


def resize_frame(frame: np.ndarray, target_width: int = 640) -> np.ndarray:
    """
    Resize frame to target width while maintaining aspect ratio.
    Helps with Mediapipe performance.

    Args:
        frame: BGR image array
        target_width: Desired width in pixels

    Returns:
        Resized frame
    """
    h, w = frame.shape[:2]
    if w <= target_width:
        return frame
    ratio = target_width / w
    target_height = int(h * ratio)
    return cv2.resize(frame, (target_width, target_height), interpolation=cv2.INTER_AREA)
