"""
SignVista ML Inference Engine

Main orchestrator that ties together:
1. Face detection (gate)
2. Keypoint extraction (Mediapipe)
3. Frame buffering (45-frame window)
4. LSTM prediction (PyTorch)

When Ishit's model weights are not available, falls back to mock predictions
so the backend can be developed and tested independently.

Ishit: Drop your model.pth into ml/models/weights/ and everything connects.
"""

import logging
import os
import random
from typing import Optional, Tuple

import numpy as np

# PyTorch is optional — mock mode works without it
# Ishit: install torch when integrating the real model
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from app.config import settings
from ml.buffer_manager import get_buffer, clear_buffer
from ml.face_detector import detect_face
from ml.keypoint_extractor import extract_keypoints
from ml.vocabulary import (
    INDEX_TO_WORD,
    WORD_LIST,
    NUM_CLASSES,
    get_word_by_index,
)

# Only import model if torch is available
if TORCH_AVAILABLE:
    from ml.models.lstm_model import ISLRecognitionLSTM, load_lstm_model

logger = logging.getLogger(__name__)

# ─── Global Model Instance ────────────────────────────────────────

_model = None  # ISLRecognitionLSTM instance when loaded
_model_loaded: bool = False


def initialize_model():
    """
    Load the LSTM model at startup.
    Falls back to mock mode if weights file is not found or torch is not installed.
    """
    global _model, _model_loaded

    if not TORCH_AVAILABLE:
        logger.warning("⚠️ PyTorch not installed — using MOCK predictions")
        logger.warning("   Ishit: pip install torch torchvision when integrating real model")
        _model = None
        _model_loaded = False
        return

    model_path = settings.MODEL_PATH

    if os.path.exists(model_path):
        try:
            _model = load_lstm_model(model_path)
            _model_loaded = True
            logger.info(f"✅ LSTM model loaded from {model_path}")
            logger.info(f"   Model classes: {NUM_CLASSES}, params: {sum(p.numel() for p in _model.parameters()):,}")
        except Exception as e:
            logger.error(f"❌ Failed to load model from {model_path}: {e}")
            _model = None
            _model_loaded = False
    else:
        logger.warning(f"⚠️ Model weights not found at '{model_path}' — using MOCK predictions")
        logger.warning(f"   Ishit: place your trained model.pth at '{model_path}'")
        _model = None
        _model_loaded = False


def is_model_loaded() -> bool:
    """Check if the real model is loaded."""
    return _model_loaded


def predict_from_raw_frame(
    session_id: str,
    frame: np.ndarray,
) -> Tuple[Optional[str], float, str]:
    """
    Full inference pipeline: frame → prediction.

    Args:
        session_id: Session identifier for buffer management
        frame: BGR image array (already decoded from base64)

    Returns:
        Tuple of (predicted_word, confidence, buffer_status)
        - predicted_word: str or None if no prediction
        - confidence: 0.0 to 1.0
        - buffer_status: 'collecting' | 'ready' | 'no_face'
    """

    # Step 1: Face detection gate
    if not detect_face(frame):
        return None, 0.0, "no_face"

    # Step 2: Extract keypoints from frame
    keypoints = extract_keypoints(frame)

    # Step 3: Append to session buffer
    buffer = get_buffer(session_id)
    buffer.append(keypoints)

    # Step 4: Check if buffer is ready
    if not buffer.is_ready:
        return None, 0.0, f"collecting ({buffer.length}/{buffer.buffer_size})"

    # Step 5: Run prediction
    if _model_loaded and _model is not None:
        word, confidence = _predict_real(buffer.get_sequence())
    else:
        word, confidence = _predict_mock()

    # Step 6: Clear buffer for next sequence (sliding window could be used instead)
    # Using a half-overlap: keep last half of buffer for continuity
    _slide_buffer(session_id)

    # Step 7: Apply confidence threshold
    if confidence < settings.CONFIDENCE_THRESHOLD:
        return None, confidence, "low_confidence"

    return word, confidence, "ready"


def _predict_real(sequence: np.ndarray) -> Tuple[str, float]:
    """Run actual LSTM inference."""
    try:
        with torch.no_grad():
            input_tensor = torch.FloatTensor(sequence)
            logits = _model(input_tensor)
            probabilities = torch.softmax(logits, dim=1)
            confidence, predicted_idx = torch.max(probabilities, dim=1)

            word = get_word_by_index(predicted_idx.item())
            return word, confidence.item()

    except Exception as e:
        logger.error(f"Model inference error: {e}")
        return None, 0.0


def _predict_mock() -> Tuple[str, float]:
    """
    Mock prediction for development/testing without Ishit's model.
    Returns a random word with random confidence.
    """
    word = random.choice(WORD_LIST[:10])  # Only core words
    confidence = random.uniform(0.55, 0.95)
    return word, round(confidence, 3)


def _slide_buffer(session_id: str):
    """
    Implement sliding window: keep the last half of the buffer
    so the next prediction doesn't need a full 45 new frames.
    """
    buffer = get_buffer(session_id)
    half = buffer.buffer_size // 2
    if buffer.length >= half:
        # Keep last `half` keypoints
        recent = list(buffer.keypoints)[-half:]
        buffer.clear()
        for kp in recent:
            buffer.append(kp)


def reset_session(session_id: str):
    """Clear all ML state for a session."""
    clear_buffer(session_id)
