
from sqlalchemy.orm import Session

from app.models.activity_log import ActivityLog


def create_activity_log(
    db: Session,
    project_id: int,
    user_id: int | None,
    action: str,
    description: str,
    task_id: int | None = None,
    details: dict | None = None,
) -> ActivityLog:
    activity = ActivityLog(
        project_id=project_id,
        task_id=task_id,
        user_id=user_id,
        action=action,
        description=description,
        details=details,
    )

    db.add(activity)

    return activity
