"""
SignVista — Profile Route

POST /api/profile       — Create/update user profile
GET  /api/profile/{sessionId} — Get user profile + welcome message

Ayush: Call POST after the onboarding form, GET when loading the dashboard.
       Welcome message comes in the user's preferred language.
"""

import time
import logging
from typing import Dict, Optional

from fastapi import APIRouter, HTTPException, Depends
from app.dependencies import get_current_user

from app.schemas import ProfileCreateRequest, ProfileResponse
from app.session_store import get_session
from ml.vocabulary import WORD_DISPLAY
from ml.sign_demos import get_sign_demo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Profile"])


from sqlalchemy.orm import Session
from app.database import get_db
from app import models

# ─── In-Memory Profile Store Removed ─────────────────────────────
# Profiles are now backed entirely by SQLite via models.User


# ─── Welcome Messages ────────────────────────────────────────────

WELCOME_MESSAGES = {
    "en": "Welcome to SignVista, {name}! 🖐️ Let's bridge the communication gap together.",
    "hi": "साइनविस्टा में आपका स्वागत है, {name}! 🖐️ आइए साथ मिलकर संवाद की खाई पाटें।",
}

WELCOME_SIGN_WORDS = ["hello", "good", "friend"]  # Words shown as sign greeting


@router.post("/profile", response_model=ProfileResponse)
async def create_profile(request: ProfileCreateRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Create or update a user profile after onboarding form.

    Ayush sends:
    ```json
    {
        "sessionId": "user-123",
        "name": "Ravi Kumar",
        "email": "ravi@example.com",
        "phone": "+91 9876543210",
        "preferred_language": "en"
    }
    ```
    """
    if not request.sessionId or not request.sessionId.strip():
        raise HTTPException(status_code=400, detail="sessionId is required")

    # Authorize
    if current_user["user_id"] != request.sessionId:
        raise HTTPException(status_code=403, detail="Unauthorized profile update")

    if not request.name or not request.name.strip():
        raise HTTPException(status_code=400, detail="Name is required")

    if not request.email or "@" not in request.email:
        raise HTTPException(status_code=400, detail="Valid email is required")

    lang = request.preferred_language.lower()
    if lang not in ("en", "hi"):
        lang = "en"

    # Store profile in DB
    user_obj = db.query(models.User).filter(models.User.user_id == request.sessionId).first()
    if not user_obj:
        raise HTTPException(status_code=404, detail="User not found in DB")
        
    user_obj.name = request.name.strip()
    user_obj.email = request.email.strip().lower()
    if request.phone:
        user_obj.phone = request.phone.strip()
    user_obj.preferred_language = lang
    
    db.commit()

    # Ensure memory session exists (for backward comp usage in games)
    get_session(request.sessionId)

    # Build welcome response
    welcome_msg = WELCOME_MESSAGES.get(lang, WELCOME_MESSAGES["en"]).format(
        name=user_obj.name
    )

    # Get sign data for welcome words
    welcome_signs = []
    for word in WELCOME_SIGN_WORDS:
        demo = get_sign_demo(word)
        if demo:
            welcome_signs.append({
                "word": word,
                "display_name": WORD_DISPLAY.get(word, word),
                "gif_url": demo["gif_url"],
                "description": demo["description"],
                "hindi_name": demo.get("hindi_name", ""),
            })

    return ProfileResponse(
        sessionId=user_obj.user_id,
        name=user_obj.name,
        email=user_obj.email,
        phone=user_obj.phone,
        preferred_language=user_obj.preferred_language,
        welcome_message=welcome_msg,
        welcome_sign_data=welcome_signs,
        created_at=user_obj.created_at,
    )


@router.get("/profile/{session_id}", response_model=ProfileResponse)
async def get_profile(session_id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Get user profile and welcome data.

    Ayush calls: GET /api/profile/user-123
    """
    if not session_id or not session_id.strip():
        raise HTTPException(status_code=400, detail="sessionId is required")

    if session_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    user_obj = db.query(models.User).filter(models.User.user_id == session_id).first()
    if not user_obj:
        raise HTTPException(status_code=404, detail="Profile not found in DB")

    lang = user_obj.preferred_language
    welcome_msg = WELCOME_MESSAGES.get(lang, WELCOME_MESSAGES["en"]).format(
        name=user_obj.name
    )

    welcome_signs = []
    for word in WELCOME_SIGN_WORDS:
        demo = get_sign_demo(word)
        if demo:
            welcome_signs.append({
                "word": word,
                "display_name": WORD_DISPLAY.get(word, word),
                "gif_url": demo["gif_url"],
                "description": demo["description"],
                "hindi_name": demo.get("hindi_name", ""),
            })

    return ProfileResponse(
        sessionId=user_obj.user_id,
        name=user_obj.name,
        email=user_obj.email,
        phone=user_obj.phone,
        preferred_language=user_obj.preferred_language,
        welcome_message=welcome_msg,
        welcome_sign_data=welcome_signs,
        created_at=user_obj.created_at,
    )
