
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.dependencies.projects import get_project_membership
from app.models.activity_log import ActivityLog
from app.models.user import User
from app.schemas.activity_logs import ActivityLogResponse

router = APIRouter(
    prefix="/projects/{project_id}/activity-logs",
    tags=["Activity Logs"],
)


@router.get("/", response_model=list[ActivityLogResponse])
def list_activity_logs(
    project_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    membership=Depends(get_project_membership),
):
    return (
        db.query(ActivityLog)
        .filter(ActivityLog.project_id == project_id)
        .order_by(ActivityLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{log_id}", response_model=ActivityLogResponse)
def get_activity_log(
    project_id: int,
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    membership=Depends(get_project_membership),
):
    activity = db.query(ActivityLog).filter(
        ActivityLog.id == log_id,
        ActivityLog.project_id == project_id,
    ).first()

    if not activity:
        raise HTTPException(
            status_code=404,
            detail="Activity log not found.",
        )

    return activity
