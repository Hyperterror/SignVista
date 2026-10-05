"""
SignVista — Profile Routes

POST /api/profile              — update the authenticated user's profile
GET  /api/profile/{sessionId}  — profile + welcome message in the preferred language
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.dependencies import get_current_user, require_own_session
from app.schemas import ProfileCreateRequest, ProfileResponse
from ml.sign_demos import get_sign_demo
from ml.vocabulary import get_display_name

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Profile"])


# ─── Welcome Messages ────────────────────────────────────────────

WELCOME_MESSAGES = {
    "en": "Welcome to SignVista, {name}! 🖐️ Let's bridge the communication gap together.",
    "hi": "साइनविस्टा में आपका स्वागत है, {name}! 🖐️ आइए साथ मिलकर संवाद की खाई पाटें।",
}

WELCOME_SIGN_WORDS = ["hello", "good", "friend"]  # Words shown as sign greeting


def _welcome_signs():
    signs = []
    for word in WELCOME_SIGN_WORDS:
        demo = get_sign_demo(word)
        if demo:
            signs.append({
                "word": word,
                "display_name": get_display_name(word),
                "gif_url": demo["gif_url"],
                "description": demo["description"],
                "hindi_name": demo.get("hindi_name", ""),
            })
    return signs


def _profile_response(user_obj: models.User) -> ProfileResponse:
    lang = user_obj.preferred_language if user_obj.preferred_language in WELCOME_MESSAGES else "en"
    return ProfileResponse(
        sessionId=user_obj.user_id,
        name=user_obj.name,
        email=user_obj.email,
        phone=user_obj.phone,
        preferred_language=lang,
        welcome_message=WELCOME_MESSAGES[lang].format(name=user_obj.name),
        welcome_sign_data=_welcome_signs(),
        created_at=user_obj.created_at,
    )


@router.post("/profile", response_model=ProfileResponse)
def update_profile(request: ProfileCreateRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update the authenticated user's profile."""
    if request.sessionId:
        require_own_session(current_user, request.sessionId)

    user_obj = db.query(models.User).filter(models.User.user_id == current_user["user_id"]).first()
    if not user_obj:
        raise HTTPException(status_code=404, detail="User not found")

    if request.email != (user_obj.email or "").lower():
        taken = db.query(models.User.id).filter(
            func.lower(models.User.email) == request.email, models.User.user_id != user_obj.user_id
        ).first()
        if taken:
            raise HTTPException(status_code=400, detail="Email already in use")

    if request.phone and request.phone != user_obj.phone:
        taken = db.query(models.User.id).filter(
            models.User.phone == request.phone, models.User.user_id != user_obj.user_id
        ).first()
        if taken:
            raise HTTPException(status_code=400, detail="Phone number already in use")
        user_obj.phone = request.phone

    user_obj.name = request.name
    user_obj.email = request.email
    user_obj.preferred_language = request.preferred_language
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Phone number already in use")
    db.refresh(user_obj)
    return _profile_response(user_obj)


@router.get("/profile/{session_id}", response_model=ProfileResponse)
def get_profile(session_id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get the authenticated user's profile and welcome data."""
    require_own_session(current_user, session_id)
    user_obj = db.query(models.User).filter(models.User.user_id == session_id).first()
    if not user_obj:
        raise HTTPException(status_code=404, detail="Profile not found")
    return _profile_response(user_obj)
