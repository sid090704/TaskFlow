
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.dependencies.tasks import get_project_task

from app.models.comment import Comment
from app.models.task import Task
from app.models.user import User

from app.schemas.comments import (
    CommentCreate,
    CommentResponse,
    CommentUpdate,
)


router = APIRouter()


@router.post(
    "/",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_comment(
    project_id: int,
    task_id: int,
    comment_data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    task: Task = Depends(get_project_task),
):
    comment = Comment(
        task_id=task.id,
        user_id=current_user.id,
        content=comment_data.content,
    )

    db.add(comment)
    db.commit()
    db.refresh(comment)

    return comment


@router.get("/", response_model=list[CommentResponse])
def get_task_comments(
    project_id: int,
    task_id: int,
    db: Session = Depends(get_db),
    task: Task = Depends(get_project_task),
):
    comments = (
        db.query(Comment)
        .filter(Comment.task_id == task.id)
        .order_by(Comment.created_at.asc())
        .all()
    )

    return comments


@router.patch("/{comment_id}", response_model=CommentResponse)
def update_comment(
    comment_id: int,
    comment_data: CommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    task: Task = Depends(get_project_task),
):
    comment = (
        db.query(Comment)
        .filter(
            Comment.id == comment_id,
            Comment.task_id == task.id,
        )
        .first()
    )

    if comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )

    if comment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own comments",
        )

    comment.content = comment_data.content

    db.commit()
    db.refresh(comment)

    return comment


@router.delete(
    "/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    task: Task = Depends(get_project_task),
):
    comment = (
        db.query(Comment)
        .filter(
            Comment.id == comment_id,
            Comment.task_id == task.id,
        )
        .first()
    )

    if comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )

    if comment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own comments",
        )

    db.delete(comment)
    db.commit()

    return None
