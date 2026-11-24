
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.dependencies.projects import get_project_membership
from app.dependencies.tasks import get_project_task
from app.models.attachment import Attachment
from app.models.project_member import ProjectMember, ProjectRole
from app.models.task import Task
from app.models.user import User
from app.schemas.attachments import AttachmentResponse
from app.services.file_storage import (
    delete_stored_file,
    get_stored_file_path,
    save_upload,
)

router = APIRouter(
    prefix="/projects/{project_id}/tasks/{task_id}/attachments",
    tags=["Attachments"],
)


@router.post(
    "/",
    response_model=AttachmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_attachment(
    project_id: int,
    task_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    task: Task = Depends(get_project_task),
):
    try:
        stored_filename, file_size = await save_upload(file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    original_filename = Path(
        (file.filename or "upload").replace("\\", "/")
    ).name

    attachment = Attachment(
        task_id=task.id,
        uploaded_by=current_user.id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        content_type=file.content_type,
        file_size=file_size,
        
    )

    try:
        db.add(attachment)
        db.commit()
        db.refresh(attachment)
    except Exception:
        db.rollback()
        delete_stored_file(stored_filename)
        raise

    return attachment


@router.get("/", response_model=list[AttachmentResponse])
def list_attachments(
    project_id: int,
    task_id: int,
    db: Session = Depends(get_db),
    task: Task = Depends(get_project_task),
):
    return (
        db.query(Attachment)
        .filter(Attachment.task_id == task.id)
        .order_by(Attachment.uploaded_at.desc())
        .all()
    )


@router.get("/{attachment_id}/download")
def download_attachment(
    project_id: int,
    task_id: int,
    attachment_id: int,
    db: Session = Depends(get_db),
    task: Task = Depends(get_project_task),
):
    attachment = db.query(Attachment).filter(
        Attachment.id == attachment_id,
        Attachment.task_id == task.id,
    ).first()

    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found.")

    file_path = get_stored_file_path(attachment.stored_filename)

    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Stored file not found.")

    return FileResponse(
        path=file_path,
        filename=attachment.original_filename,
        media_type=attachment.content_type or "application/octet-stream",
    )


@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attachment(
    project_id: int,
    task_id: int,
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    task: Task = Depends(get_project_task),
    membership: ProjectMember = Depends(get_project_membership),
):
    attachment = db.query(Attachment).filter(
        Attachment.id == attachment_id,
        Attachment.task_id == task.id,
    ).first()

    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found.")

    is_project_manager = membership.role in {
        ProjectRole.OWNER,
        ProjectRole.MANAGER,
    }
    is_uploader = attachment.uploaded_by == current_user.id

    if not (is_project_manager or is_uploader):
        raise HTTPException(
            status_code=403,
            detail="You cannot delete this attachment.",
        )

    stored_filename = attachment.stored_filename

    db.delete(attachment)
    db.commit()

    # Database metadata is deleted first. If disk cleanup fails,
    # the remaining file is an orphan and can be cleaned up later.
    try:
        delete_stored_file(stored_filename)
    except OSError:
        pass

    return None
