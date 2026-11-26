
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notifications import NotificationResponse

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)


# Retrieve notifications belonging to the logged-in user.
@router.get("/", response_model=list[NotificationResponse])
def list_notifications(
    unread_only: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Notification).filter(
        Notification.user_id == current_user.id
    )

    if unread_only:
        query = query.filter(Notification.is_read.is_(False))

    return query.order_by(
        Notification.created_at.desc()
    ).all()


# Mark one notification as read.
@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
)
def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id,
    ).first()

    if not notification:
        raise HTTPException(
            status_code=404,
            detail="Notification not found.",
        )

    if not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(notification)

    return notification


# Mark all unread notifications as read.
@router.patch("/read-all")
def mark_all_notifications_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    updated_count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read.is_(False),
    ).update(
        {
            Notification.is_read: True,
            Notification.read_at: datetime.now(timezone.utc),
        },
        synchronize_session=False,
    )

    db.commit()

    return {"updated_count": updated_count}
