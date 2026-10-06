"""
SignVista ML Inference Engine

Orchestrates, per frame:
1. Optional face-detection gate
2. One landmark extraction (MediaPipe Pose + Hands) shared by all modules
3. Detection (static letters/digits), Recognition (45-frame LSTM words) and
   Translation (YOLO + SqueezeNet, optional) modules
4. Final prediction selection (priority / highest_confidence / voting)

A standalone legacy LSTM (settings.MODEL_PATH) is used only when the
recognition module is unavailable. Mock predictions are returned only when
ALLOW_MOCK_PREDICTIONS is enabled (tests/demos).
"""

import logging
import os
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from app.config import settings
from ml.buffer_manager import delete_buffer, get_buffer, peek_buffer
from ml.config_manager import ConfigurationManager
from ml.face_detector import detect_face
from ml.keypoint_extractor import FrameLandmarks, extract_landmarks
from ml.model_loader import ModelLoader
from ml.modules import ModulePrediction
from ml.modules.detection import DetectionModule
from ml.modules.recognition import RecognitionModule
from ml.modules.translation import TranslationModule
from ml.vocabulary import (
    DETECTION_VOCAB,
    RECOGNITION_VOCAB,
    TRANSLATION_VOCAB,
    VOCABULARY,
    get_display_name,
    get_word_by_index,
)

logger = logging.getLogger(__name__)

MODULE_NAMES = ("detection", "recognition", "translation")
LEGACY_BUFFER_SUFFIX = ":legacy"

# ─── Global State ─────────────────────────────────────────────────

_model = None  # legacy standalone LSTM
_model_loaded: bool = False
_model_lock = threading.Lock()

_config_manager: Optional[ConfigurationManager] = None
_model_loader: Optional[ModelLoader] = None
_detection_module: Optional[DetectionModule] = None
_recognition_module: Optional[RecognitionModule] = None
_translation_module: Optional[TranslationModule] = None
_isl_modules_initialized: bool = False


# ─── Initialization ───────────────────────────────────────────────

def initialize_model():
    """Load the optional legacy standalone Keras model (a full model file)."""
    global _model, _model_loaded
    model_path = settings.MODEL_PATH
    if not os.path.exists(model_path):
        logger.info(f"ℹ️ No legacy LSTM at {model_path} (optional)")
        return
    try:
        import tensorflow as tf
        _model = tf.keras.models.load_model(model_path, compile=False)
        _model_loaded = True
        logger.info(f"✅ Legacy LSTM loaded from {model_path} (output={_model.output_shape})")
    except Exception as e:
        logger.error(f"❌ Failed to load legacy model from {model_path}: {e}")
        _model = None
        _model_loaded = False


def is_model_loaded() -> bool:
    """True if any real sign model can produce predictions."""
    return _model_loaded or any(m is not None for m in (_detection_module, _recognition_module, _translation_module))


def _module_config_dict(name: str) -> Dict[str, Any]:
    cfg = _config_manager.get_module_config(name)
    return {
        "confidence_threshold": cfg.confidence_threshold,
        "preprocessing_params": dict(cfg.preprocessing_params or {}),
    }


def initialize_isl_modules():
    """Load configuration and models for the enabled ISL modules."""
    global _config_manager, _model_loader
    global _detection_module, _recognition_module, _translation_module
    global _isl_modules_initialized

    try:
        _config_manager = ConfigurationManager()
        is_valid, errors = _config_manager.validate()
        if not is_valid:
            logger.warning(f"⚠️ Configuration validation errors: {errors}")

        _model_loader = ModelLoader()
        enabled = [n for n in MODULE_NAMES if _config_manager.is_module_enabled(n)]
        if not enabled:
            logger.info("ℹ️ No ISL modules enabled in configuration")
            _isl_modules_initialized = True
            return

        logger.info(f"📦 Loading ISL modules: {enabled}")
        load_results = _model_loader.load_all_models(enabled)

        if "detection" in enabled and load_results.get("detection"):
            try:
                _detection_module = DetectionModule(_model_loader.get_model("detection"), _module_config_dict("detection"))
            except Exception as e:
                logger.error(f"❌ Failed to initialize detection module: {e}")

        if "recognition" in enabled and load_results.get("recognition"):
            try:
                _recognition_module = RecognitionModule(_model_loader.get_model("recognition"), _module_config_dict("recognition"))
            except Exception as e:
                logger.error(f"❌ Failed to initialize recognition module: {e}")

        if "translation" in enabled and load_results.get("translation"):
            try:
                from app.config import REPO_ROOT
                yolo_dir = os.path.join(str(REPO_ROOT), "ISL-Unified-Project", "config", "yolo")
                _translation_module = TranslationModule(
                    model=_model_loader.get_model("translation"),
                    yolo_config=os.path.join(yolo_dir, "cross-hands.cfg"),
                    yolo_weights=os.path.join(yolo_dir, "cross-hands.weights"),
                    config=_module_config_dict("translation"),
                )
            except Exception as e:
                logger.error(f"❌ Failed to initialize translation module: {e}")

        _isl_modules_initialized = True
        logger.info("🎉 ISL modules initialization complete")
    except Exception as e:
        logger.error(f"❌ Failed to initialize ISL modules: {e}", exc_info=True)
        _isl_modules_initialized = False


def warmup() -> None:
    """Run one dummy frame through the pipeline so the first user request is fast."""
    try:
        t = time.time()
        frame = np.full((480, 640, 3), 127, dtype=np.uint8)
        extract_landmarks(frame)
        if _recognition_module is not None:
            _recognition_module._predict(np.zeros((1, _recognition_module.buffer_size, 258), np.float32))
        if _detection_module is not None:
            _detection_module._predict(np.zeros((1, 42), np.float32))
        logger.info(f"🔥 ML pipeline warmed up in {time.time() - t:.1f}s")
    except Exception as e:
        logger.warning(f"Warm-up failed (non-fatal): {e}")


def are_isl_modules_initialized() -> bool:
    return _isl_modules_initialized


def _loaded_module(name: str):
    return {"detection": _detection_module, "recognition": _recognition_module, "translation": _translation_module}[name]


def get_isl_modules_status() -> Dict[str, Any]:
    """Module status for the health endpoint."""
    if not _isl_modules_initialized or _config_manager is None:
        return {"initialized": False, "enabled_modules": [], "configuration": {}, "modules": {}}

    module_status = {}
    for name in MODULE_NAMES:
        cfg = _config_manager.get_module_config(name)
        enabled = _config_manager.is_module_enabled(name)
        module_status[name] = {
            "enabled": enabled,
            "loaded": _loaded_module(name) is not None,
            "confidence_threshold": cfg.confidence_threshold if enabled and cfg else None,
            "priority": cfg.priority if enabled and cfg else None,
        }

    return {
        "initialized": True,
        "enabled_modules": [n for n in MODULE_NAMES if _config_manager.is_module_enabled(n)],
        "configuration": {
            "prediction_strategy": _config_manager.get_prediction_strategy(),
            "fallback_to_lstm": _config_manager.config.fallback_to_existing_lstm,
            "require_face_detection": _config_manager.config.require_face_detection,
        },
        "modules": module_status,
        "legacy_lstm_loaded": _model_loaded,
        "mock_predictions": settings.ALLOW_MOCK_PREDICTIONS,
    }


# ─── Vocabulary the loaded models can actually recognize ─────────

def get_recognizable_words() -> List[str]:
    """Words/letters a loaded model can output (used for games and practice)."""
    words: List[str] = []
    if _recognition_module is not None:
        words += [v["word"] for v in RECOGNITION_VOCAB]
    elif _model_loaded:
        n = int(_model.output_shape[-1])
        words += [v["word"] for v in VOCABULARY if v["index"] < n]
    if _detection_module is not None:
        words += [v["word"] for v in DETECTION_VOCAB]
    if _translation_module is not None:
        words += [v["word"] for v in TRANSLATION_VOCAB]
    if not words and settings.ALLOW_MOCK_PREDICTIONS:
        words = ["hello"]
    return list(dict.fromkeys(words))


def get_game_word_pool() -> List[str]:
    """
    Challenge pool for games: word-level signs when available (they're the
    core experience), plus static letters/digits when only detection exists.
    """
    words = get_recognizable_words()
    phrase_words = [w for w in words if w in {v["word"] for v in RECOGNITION_VOCAB} or w in {v["word"] for v in VOCABULARY}]
    if len(phrase_words) >= 3:
        # Mix in a handful of static letters for variety when detection is loaded
        letters = [w for w in words if w not in phrase_words]
        return phrase_words + letters[:7]
    return words


_WORD_LEVEL = {v["word"].lower() for v in RECOGNITION_VOCAB} | {v["word"].lower() for v in VOCABULARY}


def is_word_level(word: str) -> bool:
    """True for word/phrase signs, False for static letters and digits."""
    return word.lower() in _WORD_LEVEL


def is_relevant_prediction(target: str, predicted: str) -> bool:
    """
    Static letter/digit predictions fire continuously while someone performs a
    word-level sign; they must not count as wrong answers for a word target.
    """
    return not (is_word_level(target) and not is_word_level(predicted))


def is_recognizable(word: str) -> bool:
    w = word.lower()
    return any(w == r.lower() for r in get_recognizable_words())


# ─── Session lifecycle ────────────────────────────────────────────

def reset_session(session_id: str) -> None:
    """Drop all per-session ML state (buffers, smoothing history)."""
    delete_buffer(session_id)
    delete_buffer(session_id + LEGACY_BUFFER_SUFFIX)
    if _detection_module is not None:
        _detection_module.reset_session(session_id)


def reset_buffer(session_id: str) -> None:
    """Start a fresh 45-frame window for this session."""
    for sid in (session_id, session_id + LEGACY_BUFFER_SUFFIX):
        buf = peek_buffer(sid)
        if buf is not None:
            buf.clear()


# ─── Orchestration ────────────────────────────────────────────────

def execute_modules_parallel(
    frame: np.ndarray,
    session_id: str,
    enabled_modules: List[str],
    landmarks: Optional[FrameLandmarks] = None,
) -> List[ModulePrediction]:
    """
    Run each enabled+loaded module and collect predictions above threshold.
    Failures are isolated per module.
    """
    predictions: List[ModulePrediction] = []
    keypoints = landmarks.to_keypoints() if landmarks is not None else None

    def _accept(name: str, pred: Optional[ModulePrediction]):
        if pred is None:
            return
        threshold = _config_manager.get_confidence_threshold(name) if _config_manager else 0.7
        if pred.confidence >= threshold:
            predictions.append(pred)
        else:
            logger.debug(f"{name}: {pred.word} {pred.confidence:.3f} < {threshold}")

    if "detection" in enabled_modules and _detection_module is not None:
        try:
            _accept("detection", _detection_module.predict(frame, session_id=session_id, landmarks=landmarks))
        except Exception as e:
            logger.error(f"Detection module failed: {e}", exc_info=True)

    if "recognition" in enabled_modules and _recognition_module is not None:
        try:
            _accept("recognition", _recognition_module.predict(frame, session_id, keypoints=keypoints))
        except Exception as e:
            logger.error(f"Recognition module failed: {e}", exc_info=True)

    if "translation" in enabled_modules and _translation_module is not None:
        try:
            _accept("translation", _translation_module.predict(frame))
        except Exception as e:
            logger.error(f"Translation module failed: {e}", exc_info=True)

    return predictions


def select_final_prediction(predictions: List[ModulePrediction], strategy: str) -> Optional[ModulePrediction]:
    """Choose the final prediction: priority, highest_confidence or voting."""
    if not predictions:
        return None
    if len(predictions) == 1:
        return predictions[0]

    if strategy == "priority":
        def prio(p: ModulePrediction) -> int:
            cfg = _config_manager.get_module_config(p.module_name) if _config_manager else None
            return cfg.priority if cfg else 999
        return min(predictions, key=prio)

    if strategy == "voting":
        votes: Dict[str, List[ModulePrediction]] = {}
        for p in predictions:
            votes.setdefault(p.word, []).append(p)
        top = max(len(v) for v in votes.values())
        winners = [w for w, v in votes.items() if len(v) == top]
        if len(winners) == 1:
            return max(votes[winners[0]], key=lambda p: p.confidence)
        return max(predictions, key=lambda p: p.confidence)

    if strategy != "highest_confidence":
        logger.warning(f"Unknown selection strategy: {strategy}, using highest_confidence")
    return max(predictions, key=lambda p: p.confidence)


def _legacy_predict(session_id: str, keypoints: np.ndarray) -> Tuple[Optional[str], float, str]:
    buffer = get_buffer(session_id + LEGACY_BUFFER_SUFFIX)
    buffer.append(keypoints)
    if not buffer.is_ready:
        return None, 0.0, f"collecting_{int(buffer.fill_ratio * 100)}%"
    with _model_lock:
        res = _model.predict(buffer.get_sequence(), verbose=0)[0]
    idx = int(np.argmax(res))
    confidence = float(res[idx])
    if confidence < settings.CONFIDENCE_THRESHOLD:
        return None, confidence, "low_confidence"
    buffer.clear()
    return get_word_by_index(idx), confidence, "ready"


def _collecting_status(session_id: str) -> Optional[str]:
    """`collecting_NN%` while the word-level buffer is still filling."""
    if _recognition_module is not None:
        buf = peek_buffer(session_id)
        if buf is None or not buf.is_ready:
            ratio = buf.fill_ratio if buf is not None else 0.0
            return f"collecting_{int(ratio * 100)}%"
    return None


def predict_from_raw_frame(
    session_id: str,
    frame: np.ndarray,
    return_landmarks: bool = False,
    return_module_details: bool = False,
) -> Tuple[Optional[str], float, str, Optional[FrameLandmarks], Optional[Dict[str, Any]]]:
    """
    Full inference pipeline for one frame.

    Returns (word, confidence, status, landmarks, module_details):
    - status: "ready" | "collecting_NN%" | "low_confidence" | "no_hands" |
              "no_face" | "no_model" | "landmarks_unavailable" | "mock_ready"
    - landmarks: FrameLandmarks when return_landmarks=True
    """
    start_time = time.time()
    module_details: Optional[Dict[str, Any]] = None

    require_face = _config_manager.config.require_face_detection if _config_manager else False
    if require_face and not detect_face(frame):
        return None, 0.0, "no_face", None, module_details

    if not is_model_loaded():
        if settings.ALLOW_MOCK_PREDICTIONS:
            return "hello", 0.95, "mock_ready", None, module_details
        return None, 0.0, "no_model", None, module_details

    landmarks = extract_landmarks(frame)
    if landmarks is None:
        return None, 0.0, "landmarks_unavailable", None, module_details
    out_landmarks = landmarks if return_landmarks else None

    enabled = [n for n in MODULE_NAMES if _config_manager and _config_manager.is_module_enabled(n) and _loaded_module(n) is not None]
    predictions: List[ModulePrediction] = []
    if enabled:
        predictions = execute_modules_parallel(frame, session_id, enabled, landmarks)
    elif _model_loaded and (_config_manager is None or _config_manager.config.fallback_to_existing_lstm):
        word, conf, status = _legacy_predict(session_id, landmarks.to_keypoints())
        return word, conf, status, out_landmarks, module_details

    total_time = time.time() - start_time
    if total_time > 0.2:
        logger.debug(f"Frame processing took {total_time:.3f}s (modules: {enabled})")

    if return_module_details:
        module_details = {
            "active_modules": enabled,
            "predictions": [
                {
                    "module": p.module_name,
                    "word": p.word,
                    "display_name": p.display_name,
                    "confidence": p.confidence,
                    "class_index": p.class_index,
                }
                for p in predictions
            ],
            "preprocessing_times": {p.module_name: p.preprocessing_time for p in predictions},
            "inference_times": {p.module_name: p.inference_time for p in predictions},
            "total_time": total_time,
            "selected": None,
        }

    if predictions:
        strategy = _config_manager.get_prediction_strategy()
        selected = select_final_prediction(predictions, strategy)
        if module_details is not None:
            module_details["selected"] = {"module": selected.module_name, "reason": f"strategy_{strategy}"}
        return selected.word, selected.confidence, "ready", out_landmarks, module_details

    status = _collecting_status(session_id)
    if status is None:
        status = "no_hands" if not landmarks.has_hands else "low_confidence"
    return None, 0.0, status, out_landmarks, module_details


def display_name_for(word: Optional[str]) -> Optional[str]:
    return get_display_name(word) if word else None
