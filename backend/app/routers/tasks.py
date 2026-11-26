
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.dependencies.projects import get_project_membership,require_project_roles
from app.dependencies.tasks import get_project_task

from app.models.project_member import ProjectMember,ProjectRole
from app.models.task import Task,TaskPriority, TaskStatus
from app.models.user import User

from app.schemas.tasks import TaskCreate, TaskResponse, TaskUpdate

from app.services.activity_service import create_activity_log
from app.services.notification_service import create_notification

router = APIRouter()


@router.post(
    "/",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_task(
    project_id: int,
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    membership: ProjectMember = Depends(get_project_membership),
):
    # If an assignee is provided, verify project membership.
    if task_data.assignee_id is not None:
        assignee_membership = (
            db.query(ProjectMember)
            .filter(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == task_data.assignee_id,
            )
            .first()
        )

        if assignee_membership is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignee must be a member of this project",
            )

    task = Task(
        project_id=project_id,
        title=task_data.title,
        description=task_data.description,
        priority=task_data.priority,
        assignee_id=task_data.assignee_id,
        due_date=task_data.due_date,
        creator_id=current_user.id,
    )

    db.add(task)
    db.flush()
    
    create_activity_log(
        db=db,
        project_id=project_id,
        user_id=current_user.id,
        task_id=task.id,
        action="TASK_CREATED",
        description=f'Created task "{task.title}"',
        details={
            "title": task.title,
            "priority": task.priority.value,
            "assignee_id": task.assignee_id,
        },
    )
    # Notify the assignee, but don't notify the creator
    # if they assigned the task to themselves.
    if task.assignee_id is not None and task.assignee_id != current_user.id:
        create_notification(
            db=db,
            user_id=task.assignee_id,
            actor_id=current_user.id,
            project_id=project_id,
            task_id=task.id,
            notification_type="TASK_ASSIGNED",
            message=f'You have been assigned a task: {task.title}',
        )
    db.commit()
    db.refresh(task)
    return task  

 


@router.get("/", response_model=list[TaskResponse])
def get_project_tasks(
    project_id: int,
    status_filter: TaskStatus | None = None,
    priority_filter: TaskPriority | None = None,
    assignee_id: int | None = None,
    db: Session = Depends(get_db),
    membership: ProjectMember = Depends(get_project_membership),
):
    query = db.query(Task).filter(
        Task.project_id == project_id
    )

    # Filter tasks by status, if provided.
    if status_filter is not None:
        query = query.filter(Task.status == status_filter)

    # Filter tasks by priority, if provided.
    if priority_filter is not None:
        query = query.filter(Task.priority == priority_filter)

    # Filter tasks by assignee, if provided.
    if assignee_id is not None:
        query = query.filter(Task.assignee_id == assignee_id)

    tasks = query.order_by(Task.created_at.desc()).all()

    return tasks



@router.get("/{task_id}", response_model=TaskResponse)
def get_task_details(
    task: Task = Depends(get_project_task),
):
    return task




@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(
    project_id: int,
    task_data: TaskUpdate,
    task: Task = Depends(get_project_task),
    db: Session = Depends(get_db),
):
    update_data = task_data.model_dump(exclude_unset=True)

    # Validate the assignee if the field was provided.
    if "assignee_id" in update_data:
        assignee_id = update_data["assignee_id"]

        if assignee_id is not None:
            membership = (
                db.query(ProjectMember)
                .filter(
                    ProjectMember.project_id == project_id,
                    ProjectMember.user_id == assignee_id,
                )
                .first()
            )

            if membership is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Assignee must be a member of this project",
                )

    # Handle task completion timestamps.
    if "status" in update_data:
        new_status = update_data["status"]

        if new_status == TaskStatus.DONE:
            if task.status != TaskStatus.DONE:
                task.completed_at = datetime.now(timezone.utc)

        else:
            task.completed_at = None

    # Apply the requested changes.
    for field, value in update_data.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)

    return task


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_task(
    task: Task = Depends(get_project_task),
    db: Session = Depends(get_db),
    membership: ProjectMember = Depends(
        require_project_roles(ProjectRole.OWNER, ProjectRole.MANAGER)
    ),
):
    db.delete(task)
    db.commit()

    return None
