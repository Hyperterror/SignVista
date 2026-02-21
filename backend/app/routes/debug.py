"""
Debug endpoint for ISL detection analysis.
"""

import logging
import numpy as np
from fastapi import APIRouter, HTTPException

from app.schemas import RecognizeFrameRequest
from app.utils.frame_utils import decode_base64_frame, validate_frame, resize_frame, FrameDecodeError
from ml.inference import _detection_module
from ml.vocabulary import get_word_by_module_index

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/debug", tags=["Debug"])


@router.post("/analyze-detection")
async def analyze_detection(request: RecognizeFrameRequest):
    """
    Analyze detection model predictions in detail.
    Returns top 5 predictions with confidence scores.
    """
    if not request.sessionId or not request.sessionId.strip():
        raise HTTPException(status_code=400, detail="sessionId is required")

    # Decode frame
    try:
        frame = decode_base64_frame(request.frame)
    except FrameDecodeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not validate_frame(frame):
        raise HTTPException(status_code=400, detail="Invalid frame")

    frame = resize_frame(frame, target_width=640)

    if _detection_module is None:
        raise HTTPException(status_code=503, detail="Detection module not initialized")

    try:
        # Extract landmarks
        landmarks = _detection_module.extract_hand_landmarks(frame)
        
        if landmarks is None:
            return {
                "status": "no_hands",
                "message": "No hands detected in frame"
            }

        # Preprocess
        processed = _detection_module.preprocess_landmarks(landmarks)
        
        # Get raw predictions
        predictions = _detection_module.model.predict(processed, verbose=0)[0]
        
        # Get top 5 predictions
        top_5_indices = np.argsort(predictions)[-5:][::-1]
        top_5 = []
        
        for idx in top_5_indices:
            word = get_word_by_module_index("detection", int(idx))
            top_5.append({
                "rank": len(top_5) + 1,
                "class_index": int(idx),
                "word": word,
                "confidence": float(predictions[idx]),
                "percentage": f"{float(predictions[idx]) * 100:.1f}%"
            })
        
        # Calculate confidence margin
        confidence_margin = top_5[0]["confidence"] - top_5[1]["confidence"] if len(top_5) > 1 else 0
        
        return {
            "status": "success",
            "top_prediction": top_5[0],
            "confidence_margin": round(confidence_margin, 3),
            "margin_percentage": f"{confidence_margin * 100:.1f}%",
            "top_5_predictions": top_5,
            "threshold": _detection_module.confidence_threshold,
            "passes_threshold": top_5[0]["confidence"] >= _detection_module.confidence_threshold,
            "passes_margin_check": confidence_margin >= 0.15,
            "analysis": {
                "prediction_quality": "excellent" if confidence_margin > 0.3 else "good" if confidence_margin > 0.15 else "poor",
                "recommendation": "Clear sign" if confidence_margin > 0.15 else "Try making the sign more distinct"
            }
        }
        
    except Exception as e:
        logger.error(f"Detection analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
