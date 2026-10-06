"""
SignVista Frame Buffer Manager

Per-session sliding windows of keypoint vectors for the word-level LSTM
(it needs BUFFER_SIZE consecutive frames before it can predict).

Buffers are evicted after a period of inactivity so abandoned sessions and
finished games don't accumulate in memory.
"""

import logging
import threading
import time
from collections import deque
from typing import Dict, Optional

import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)

KEYPOINT_DIM = 258  # 132 Pose + 63 Left Hand + 63 Right Hand
BUFFER_IDLE_TTL_SECONDS = 10 * 60


class FrameBuffer:
    """Buffer for a single session's keypoint sequence."""

    def __init__(self, buffer_size: int = settings.BUFFER_SIZE):
        self.buffer_size = buffer_size
        self.keypoints: deque = deque(maxlen=buffer_size)
        self.last_used = time.monotonic()
        self._lock = threading.Lock()

    def append(self, keypoints: np.ndarray):
        """Add a keypoint vector to the buffer."""
        if keypoints.shape[0] != KEYPOINT_DIM:
            logger.warning(f"Expected {KEYPOINT_DIM}-dim keypoints, got {keypoints.shape[0]}")
            return
        with self._lock:
            self.keypoints.append(keypoints)
            self.last_used = time.monotonic()

    @property
    def is_ready(self) -> bool:
        return len(self.keypoints) >= self.buffer_size

    @property
    def fill_ratio(self) -> float:
        return len(self.keypoints) / self.buffer_size

    def get_sequence(self) -> Optional[np.ndarray]:
        """Shape (1, buffer_size, KEYPOINT_DIM), or None if not ready."""
        with self._lock:
            if len(self.keypoints) < self.buffer_size:
                return None
            sequence = np.array(list(self.keypoints), dtype=np.float32)
        return np.expand_dims(sequence, axis=0)

    def clear(self):
        with self._lock:
            self.keypoints.clear()

    @property
    def length(self) -> int:
        return len(self.keypoints)


# ─── Global Buffer Store (per session) ────────────────────────────

_buffers: Dict[str, FrameBuffer] = {}
_lock = threading.Lock()
_last_sweep = 0.0


def _sweep(now: float) -> None:
    global _last_sweep
    if now - _last_sweep < 60:
        return
    _last_sweep = now
    stale = [sid for sid, b in _buffers.items() if now - b.last_used > BUFFER_IDLE_TTL_SECONDS]
    for sid in stale:
        del _buffers[sid]


def get_buffer(session_id: str, buffer_size: Optional[int] = None) -> FrameBuffer:
    """Get or create a frame buffer for a session."""
    size = buffer_size or settings.BUFFER_SIZE
    now = time.monotonic()
    with _lock:
        _sweep(now)
        buf = _buffers.get(session_id)
        if buf is None or buf.buffer_size != size:
            buf = FrameBuffer(size)
            _buffers[session_id] = buf
        buf.last_used = now
        return buf


def peek_buffer(session_id: str) -> Optional[FrameBuffer]:
    """Return an existing buffer without creating one."""
    return _buffers.get(session_id)


def clear_buffer(session_id: str):
    buf = _buffers.get(session_id)
    if buf is not None:
        buf.clear()


def delete_buffer(session_id: str):
    with _lock:
        _buffers.pop(session_id, None)


def buffer_count() -> int:
    return len(_buffers)
