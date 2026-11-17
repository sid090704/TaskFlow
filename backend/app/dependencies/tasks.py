
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.dependencies.projects import get_project_membership
from app.models.project_member import ProjectMember
from app.models.task import Task


def get_project_task(
    project_id: int,
    task_id: int,
    db: Session = Depends(get_db),
    membership: ProjectMember = Depends(get_project_membership),
) -> Task:

    task = (
        db.query(Task)
        .filter(
            Task.id == task_id,
            Task.project_id == project_id,
        )
        .first()
    )

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return task
