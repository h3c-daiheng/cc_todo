import uuid
from pathlib import Path

import magic
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from config import ALLOWED_MIME_TYPES, MAX_UPLOAD_SIZE, UPLOAD_DIR
from database import get_db
from dependencies import ensure_task_view_permission, get_current_user
from models import Attachment, Task, User

router = APIRouter(tags=["attachments"])


def ok(data):
    return {"code": 0, "message": "ok", "data": data}


def get_task_or_404(db: Session, task_id: int) -> Task:
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")
    return task


def get_attachment_or_404(db: Session, attachment_id: int) -> Attachment:
    attachment = db.get(Attachment, attachment_id)
    if not attachment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="附件不存在")
    return attachment


def can_delete_attachment(db: Session, attachment: Attachment, user: User) -> bool:
    if user.is_admin or attachment.uploaded_by == user.id:
        return True
    task = db.get(Task, attachment.task_id)
    if task and (task.created_by == user.id):
        return True
    # task editor: check edit permission
    from dependencies import ensure_task_edit_permission
    try:
        ensure_task_edit_permission(db, task, user)
        return True
    except HTTPException:
        return False


@router.post("/tasks/{task_id}/attachments")
async def upload_attachment(
    task_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = get_task_or_404(db, task_id)
    ensure_task_view_permission(db, task, current_user)

    # Read file contents
    contents = await file.read()

    # Check file size
    if len(contents) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件过大，最大允许 {MAX_UPLOAD_SIZE // (1024 * 1024)}MB",
        )

    # Detect real MIME type using python-magic
    detected_mime = magic.from_buffer(contents, mime=True)
    if detected_mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型: {detected_mime}",
        )

    # Save file with uuid name, preserving original extension
    original_filename = file.filename or "upload"
    suffix = Path(original_filename).suffix
    stored_name = f"{uuid.uuid4().hex}{suffix}"
    file_path = UPLOAD_DIR / stored_name

    with open(file_path, "wb") as f:
        f.write(contents)

    attachment = Attachment(
        task_id=task_id,
        uploaded_by=current_user.id,
        filename=original_filename,
        stored_name=stored_name,
        file_size=len(contents),
        mime_type=detected_mime,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)

    return ok({
        "id": attachment.id,
        "filename": attachment.filename,
        "file_size": attachment.file_size,
        "mime_type": attachment.mime_type,
        "uploaded_by": attachment.uploaded_by,
        "created_at": attachment.created_at.isoformat() if attachment.created_at else None,
    })


@router.get("/attachments/{attachment_id}/download")
def download_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attachment = get_attachment_or_404(db, attachment_id)

    # Check user can view the task this attachment belongs to
    task = get_task_or_404(db, attachment.task_id)
    ensure_task_view_permission(db, task, current_user)

    file_path = UPLOAD_DIR / attachment.stored_name
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在")

    return FileResponse(
        path=str(file_path),
        filename=attachment.filename,
        media_type=attachment.mime_type,
    )


@router.delete("/attachments/{attachment_id}")
def delete_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attachment = get_attachment_or_404(db, attachment_id)

    if not can_delete_attachment(db, attachment, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权删除该附件")

    # Remove physical file
    file_path = UPLOAD_DIR / attachment.stored_name
    if file_path.exists():
        file_path.unlink()

    db.delete(attachment)
    db.commit()
    return ok(None)
