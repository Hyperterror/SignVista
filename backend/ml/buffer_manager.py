"""
SignVista Frame Buffer Manager

Manages per-session buffers of keypoint sequences.
The LSTM needs 45 consecutive frames before it can make a prediction.
This module accumulates keypoints frame-by-frame until the buffer is full.

Ishit: BUFFER_SIZE must match your LSTM's expected sequence length.
"""

import logging
from collections import deque
from typing import Dict, Optional

import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)

# Input dimensions
KEYPOINT_DIM = 258  # 132 Pose + 63 Left Hand + 63 Right Hand


class FrameBuffer:
    """Buffer for a single session's keypoint sequence."""

    def __init__(self, buffer_size: int = settings.BUFFER_SIZE):
        self.buffer_size = buffer_size
        self.keypoints: deque = deque(maxlen=buffer_size)

    def append(self, keypoints: np.ndarray):
        """Add a keypoint vector to the buffer."""
        if keypoints.shape[0] != KEYPOINT_DIM:
            logger.warning(f"Expected {KEYPOINT_DIM}-dim keypoints, got {keypoints.shape[0]}")
            return
        self.keypoints.append(keypoints)

    @property
    def is_ready(self) -> bool:
        """True when buffer has enough frames for LSTM prediction."""
        return len(self.keypoints) >= self.buffer_size

    @property
    def fill_ratio(self) -> float:
        """How full the buffer is (0.0 to 1.0)."""
        return len(self.keypoints) / self.buffer_size

    def get_sequence(self) -> Optional[np.ndarray]:
        """
        Get the sequence as a numpy array for LSTM input.

        Returns:
            np.ndarray of shape (1, buffer_size, KEYPOINT_DIM) or None if not ready
        """
        if not self.is_ready:
            return None

        sequence = np.array(list(self.keypoints), dtype=np.float32)
        # Add batch dimension: (1, 45, 99)
        return np.expand_dims(sequence, axis=0)

    def clear(self):
        """Clear the buffer."""
        self.keypoints.clear()

    @property
    def length(self) -> int:
        return len(self.keypoints)


# ─── Global Buffer Store (per session) ────────────────────────────

_buffers: Dict[str, FrameBuffer] = {}


def get_buffer(session_id: str) -> FrameBuffer:
    """Get or create a frame buffer for a session."""
    if session_id not in _buffers:
        _buffers[session_id] = FrameBuffer()
    return _buffers[session_id]


def clear_buffer(session_id: str):
    """Clear a session's buffer."""
    if session_id in _buffers:
        _buffers[session_id].clear()


def delete_buffer(session_id: str):
    """Remove a session's buffer entirely."""
    _buffers.pop(session_id, None)
