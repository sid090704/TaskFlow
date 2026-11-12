from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.models.project import Project
from app.models.project_member import ProjectMember, ProjectRole
from app.models.user import User
from app.schemas.projects import ProjectCreate, ProjectResponse


router = APIRouter()


@router.post(
    "/",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        project = Project(
            name=project_data.name,
            description=project_data.description,
            owner_id=current_user.id,
        )

        db.add(project)
        db.flush()

        membership = ProjectMember(
            project_id=project.id,
            user_id=current_user.id,
            role=ProjectRole.OWNER,
        )

        db.add(membership)
        db.commit()
        db.refresh(project)

        return project

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create project",
        )
        


@router.get("/", response_model=list[ProjectResponse])
def get_my_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    projects = (
        db.query(Project)
        .join(
            ProjectMember,
            Project.id == ProjectMember.project_id,
        )
        .filter(ProjectMember.user_id == current_user.id)
        .order_by(Project.created_at.desc())
        .all()
    )

    return projects
