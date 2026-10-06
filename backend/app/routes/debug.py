"""
Debug endpoint for ISL detection analysis.

Mounted only when ENABLE_DEBUG_ROUTES=true, and always requires authentication.
"""

import logging
from typing import Dict

import numpy as np
from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_current_user
from app.schemas import RecognizeFrameRequest
from app.utils.frame_utils import FrameDecodeError, decode_base64_frame, resize_frame, validate_frame
from ml import inference
from ml.keypoint_extractor import extract_landmarks
from ml.vocabulary import get_word_by_module_index

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/debug", tags=["Debug"])


@router.post("/analyze-detection")
def analyze_detection(request: RecognizeFrameRequest, current_user: Dict = Depends(get_current_user)):
    """Top-5 detection predictions with confidence scores for one frame."""
    try:
        frame = decode_base64_frame(request.frame)
    except FrameDecodeError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if not validate_frame(frame):
        raise HTTPException(status_code=400, detail="Invalid frame")
    frame = resize_frame(frame, target_width=640)

    module = inference._detection_module
    if module is None:
        raise HTTPException(status_code=503, detail="Detection module not initialized")

    landmarks = extract_landmarks(frame)
    if landmarks is None or not landmarks.hands:
        return {"status": "no_hands", "message": "No hands detected in frame"}

    try:
        features = module.hand_to_features(landmarks.hands[0], landmarks.image_width, landmarks.image_height)
        predictions = module.model.predict(module.preprocess_landmarks(features), verbose=0)[0]
    except Exception:
        logger.exception("Detection analysis failed")
        raise HTTPException(status_code=500, detail="Detection analysis failed") from None

    top_5 = [
        {
            "rank": rank + 1,
            "class_index": int(idx),
            "word": get_word_by_module_index("detection", int(idx)),
            "confidence": float(predictions[idx]),
            "percentage": f"{float(predictions[idx]) * 100:.1f}%",
        }
        for rank, idx in enumerate(np.argsort(predictions)[-5:][::-1])
    ]
    margin = top_5[0]["confidence"] - top_5[1]["confidence"] if len(top_5) > 1 else 0.0

    return {
        "status": "success",
        "top_prediction": top_5[0],
        "confidence_margin": round(margin, 3),
        "margin_percentage": f"{margin * 100:.1f}%",
        "top_5_predictions": top_5,
        "threshold": module.confidence_threshold,
        "passes_threshold": top_5[0]["confidence"] >= module.confidence_threshold,
        "passes_margin_check": margin >= module.min_margin,
        "analysis": {
            "prediction_quality": "excellent" if margin > 0.3 else "good" if margin > module.min_margin else "poor",
            "recommendation": "Clear sign" if margin > module.min_margin else "Try making the sign more distinct",
        },
    }
