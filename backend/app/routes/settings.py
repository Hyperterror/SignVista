"""
SignVista — Settings Route

GET /api/settings/{sessionId}
PUT /api/settings

Manages user application preferences in the SQLite database.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import time

from app.dependencies import get_current_user
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/api", tags=["Settings"])


@router.get("/settings/{session_id}", response_model=schemas.UserSettingsResponse)
async def get_settings(session_id: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Retrieve user settings."""
    # Ensure current user matches the requested session id (user_id)
    if current_user["user_id"] != session_id:
        raise HTTPException(status_code=403, detail="Unauthorized access to settings")

    settings = db.query(models.UserSettings).filter(models.UserSettings.user_id == session_id).first()
    if not settings:
        # Create default settings if none exist
        settings = models.UserSettings(user_id=current_user["user_id"])
        db.add(settings)
        db.commit()
        db.refresh(settings)

    return schemas.UserSettingsResponse(
        theme=settings.theme,
        notifications_enabled=settings.notifications_enabled,
        sound_enabled=settings.sound_enabled,
        daily_goal_minutes=settings.daily_goal_minutes,
        updated_at=settings.updated_at
    )


@router.put("/settings", response_model=schemas.UserSettingsResponse)
async def update_settings(request: schemas.UserSettingsUpdate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update user settings."""
    settings = db.query(models.UserSettings).filter(models.UserSettings.user_id == current_user["user_id"]).first()
    if not settings:
        settings = models.UserSettings(user_id=current_user["user_id"])
        db.add(settings)

    if request.theme is not None:
        settings.theme = request.theme
    if request.notifications_enabled is not None:
        settings.notifications_enabled = request.notifications_enabled
    if request.sound_enabled is not None:
        settings.sound_enabled = request.sound_enabled
    if request.daily_goal_minutes is not None:
        settings.daily_goal_minutes = request.daily_goal_minutes
        
    settings.updated_at = time.time()
    
    db.commit()
    db.refresh(settings)

    return schemas.UserSettingsResponse(
        theme=settings.theme,
        notifications_enabled=settings.notifications_enabled,
        sound_enabled=settings.sound_enabled,
        daily_goal_minutes=settings.daily_goal_minutes,
        updated_at=settings.updated_at
    )
