
from sqlalchemy.orm import Session

from app.models.notification import Notification


def create_notification(
    db: Session,
    user_id: int,
    notification_type: str,
    message: str,
    project_id: int | None = None,
    task_id: int | None = None,
    actor_id: int | None = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        project_id=project_id,
        task_id=task_id,
        actor_id=actor_id,
        notification_type=notification_type,
        message=message,
    )

    db.add(notification)

    return notification
