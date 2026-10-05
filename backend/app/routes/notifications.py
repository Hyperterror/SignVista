"""
SignVista — Notifications Route

GET /api/notifications/{sessionId}
POST /api/notifications/read/{notification_id}
POST /api/notifications/read_all
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, require_own_session
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/api", tags=["Notifications"])


@router.get("/notifications/{session_id}", response_model=schemas.NotificationsListResponse)
def get_notifications(
    session_id: str,
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fetch user logic notifications."""
    require_own_session(current_user, session_id)

    notifications = db.query(models.Notification).filter(
        models.Notification.user_id == current_user["user_id"]
    ).order_by(models.Notification.timestamp.desc()).limit(limit).all()

    unread_count = db.query(models.Notification).filter(
        models.Notification.user_id == current_user["user_id"],
        models.Notification.is_read.is_(False),
    ).count()

    return schemas.NotificationsListResponse(
        unread_count=unread_count,
        notifications=[
            schemas.NotificationResponse(
                id=n.id,
                title=n.title,
                message=n.message,
                type=n.type,
                is_read=n.is_read,
                timestamp=n.timestamp,
                action_url=n.action_url
            ) for n in notifications
        ]
    )


@router.post("/notifications/read/{notification_id}")
def mark_read(notification_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Mark a specific notification as read."""
    notification = db.query(models.Notification).filter(
        models.Notification.id == notification_id,
        models.Notification.user_id == current_user["user_id"]
    ).first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    if not notification.is_read:
        notification.is_read = True
        db.commit()

    return {"status": "ok"}


@router.post("/notifications/read_all")
def mark_all_read(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Mark all notifications as read for the user."""
    unread_notifications = db.query(models.Notification).filter(
        models.Notification.user_id == current_user["user_id"],
        models.Notification.is_read == False
    ).all()

    for n in unread_notifications:
        n.is_read = True
        
    if unread_notifications:
        db.commit()

    return {"status": "ok", "marked_count": len(unread_notifications)}
