
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.dependencies.projects import (
    get_project_membership,
    require_project_roles,
)
from app.dependencies.tasks import get_project_task

from app.models.label import Label
from app.models.project_member import ProjectMember, ProjectRole
from app.models.task import Task

from app.schemas.labels import LabelCreate, LabelResponse


router = APIRouter()


# Create a label within a project.
@router.post(
    "/labels/",
    response_model=LabelResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_label(
    project_id: int,
    label_data: LabelCreate,
    db: Session = Depends(get_db),
    membership: ProjectMember = Depends(get_project_membership),
):
    label = Label(
        project_id=project_id,
        name=label_data.name,
        color=label_data.color,
    )

    db.add(label)

    try:
        db.commit()
        db.refresh(label)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A label with this name already exists in this project",
        )

    return label


# List all labels belonging to a project.
@router.get(
    "/labels/",
    response_model=list[LabelResponse],
)
def get_project_labels(
    project_id: int,
    db: Session = Depends(get_db),
    membership: ProjectMember = Depends(get_project_membership),
):
    return (
        db.query(Label)
        .filter(Label.project_id == project_id)
        .order_by(Label.name.asc())
        .all()
    )


# Delete a project label.
@router.delete(
    "/labels/{label_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_label(
    project_id: int,
    label_id: int,
    db: Session = Depends(get_db),
    membership: ProjectMember = Depends(
        require_project_roles(ProjectRole.OWNER, ProjectRole.MANAGER)
    ),
):
    label = (
        db.query(Label)
        .filter(
            Label.id == label_id,
            Label.project_id == project_id,
        )
        .first()
    )

    if label is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Label not found",
        )

    db.delete(label)
    db.commit()

    return None


# Attach a label to a task.
@router.post(
    "/tasks/{task_id}/labels/{label_id}",
    response_model=LabelResponse,
)
def attach_label_to_task(
    project_id: int,
    label_id: int,
    task: Task = Depends(get_project_task),
    db: Session = Depends(get_db),
    membership: ProjectMember = Depends(get_project_membership),
):
    label = (
        db.query(Label)
        .filter(
            Label.id == label_id,
            Label.project_id == project_id,
        )
        .first()
    )

    if label is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Label not found in this project",
        )

    if label not in task.labels:
        task.labels.append(label)
        db.commit()

    return label


# Remove a label from a task.
@router.delete(
    "/tasks/{task_id}/labels/{label_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_label_from_task(
    project_id: int,
    label_id: int,
    task: Task = Depends(get_project_task),
    db: Session = Depends(get_db),
    membership: ProjectMember = Depends(get_project_membership),
):
    label = (
        db.query(Label)
        .filter(
            Label.id == label_id,
            Label.project_id == project_id,
        )
        .first()
    )

    if label is None or label not in task.labels:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Label not found on this task",
        )

    task.labels.remove(label)
    db.commit()

    return None
