from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from database import get_db
from dependencies import (
    ensure_task_assignee_permission,
    ensure_task_delete_permission,
    ensure_task_edit_permission,
    ensure_task_status_permission,
    ensure_task_view_permission,
    get_current_user,
    is_team_member,
)
from models import Task, TaskLabel, Team, User

router = APIRouter(prefix="/tasks", tags=["tasks"])

VALID_STATUSES = {"pending", "in_progress", "done"}
VALID_PRIORITIES = {"low", "medium", "high"}


def ok(data):
    return {"code": 0, "message": "ok", "data": data}


class TaskCreatePayload(BaseModel):
    title: str
    description: str | None = None
    priority: str = "medium"
    due_date: date | None = None
    start_date: date | None = None
    assigned_to: int | None = None
    team_id: int | None = None
    labels: list[str] = []


class TaskUpdatePayload(BaseModel):
    title: str | None = None
    description: str | None = None
    priority: str | None = None
    due_date: date | None = None
    start_date: date | None = None
    labels: list[str] | None = None


class TaskStatusPayload(BaseModel):
    status: str


class TaskAssigneePayload(BaseModel):
    assigned_to: int | None = None


def normalize_labels(labels: list[str]) -> list[str]:
    seen = set()
    result = []
    for label in labels:
        value = label.strip()
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def serialize_task(task: Task, include_detail: bool = False) -> dict:
    result = {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "start_date": task.start_date.isoformat() if task.start_date else None,
        "created_by": task.created_by,
        "assigned_to": task.assigned_to,
        "team_id": task.team_id,
        "labels": [item.label for item in sorted(task.labels, key=lambda item: item.label)],
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
    }
    if include_detail:
        result["comments"] = [
            {
                "id": c.id,
                "user_id": c.user_id,
                "content": c.content,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in task.comments
        ]
        result["attachments"] = [
            {
                "id": a.id,
                "filename": a.filename,
                "file_size": a.file_size,
                "mime_type": a.mime_type,
                "uploaded_by": a.uploaded_by,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in task.attachments
        ]
    return result


def get_task_or_404(db: Session, task_id: int) -> Task:
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")
    return task


def get_team_or_404(db: Session, team_id: int) -> Team:
    team = db.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="团队不存在")
    return team


def validate_priority(priority: str):
    if priority not in VALID_PRIORITIES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="优先级必须是 low、medium、high 之一")


def validate_status(status_value: str):
    if status_value not in VALID_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="状态必须是 pending、in_progress、done 之一")


def validate_title(title: str | None):
    if title is None or not title.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="标题不能为空")


def validate_assignee(db: Session, task_team_id: int | None, assigned_to: int | None) -> int | None:
    if assigned_to is None:
        return None

    assignee = db.get(User, assigned_to)
    if not assignee or not assignee.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="负责人不存在")

    if task_team_id and not is_team_member(db, task_team_id, assigned_to):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="团队任务负责人必须是团队成员")

    return assigned_to


def replace_labels(db: Session, task: Task, labels: list[str]):
    db.query(TaskLabel).filter(TaskLabel.task_id == task.id).delete()
    for label in normalize_labels(labels):
        db.add(TaskLabel(task_id=task.id, label=label))
    db.flush()


@router.get("")
def list_tasks(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    status_value: str | None = Query(default=None, alias="status"),
    priority: str | None = None,
    assigned_to: int | None = None,
    label: str | None = None,
    due_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Task)

    if not current_user.is_admin:
        member_team_ids = db.query(Team.id).filter(Team.members.any(user_id=current_user.id))
        query = query.filter(
            or_(
                Task.created_by == current_user.id,
                Task.assigned_to == current_user.id,
                Task.team_id.in_(member_team_ids),
            )
        )

    if status_value:
        validate_status(status_value)
        query = query.filter(Task.status == status_value)
    if priority:
        validate_priority(priority)
        query = query.filter(Task.priority == priority)
    if assigned_to is not None:
        query = query.filter(Task.assigned_to == assigned_to)
    if label:
        query = query.join(TaskLabel).filter(TaskLabel.label == label)
    if due_date is not None:
        query = query.filter(Task.due_date == due_date)

    total = query.count()
    items = query.order_by(Task.id.asc()).offset((page - 1) * size).limit(size).all()
    return ok({"total": total, "page": page, "size": size, "items": [serialize_task(item) for item in items]})


@router.post("")
def create_task(
    payload: TaskCreatePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    validate_title(payload.title)
    validate_priority(payload.priority)

    if payload.team_id is not None:
        team = get_team_or_404(db, payload.team_id)
        if not current_user.is_admin and not is_team_member(db, team.id, current_user.id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权在该团队下创建任务")

    assigned_to = validate_assignee(db, payload.team_id, payload.assigned_to)

    task = Task(
        title=payload.title.strip(),
        description=payload.description,
        status="pending",
        priority=payload.priority,
        due_date=payload.due_date,
        start_date=payload.start_date,
        created_by=current_user.id,
        assigned_to=assigned_to,
        team_id=payload.team_id,
    )
    db.add(task)
    db.flush()
    replace_labels(db, task, payload.labels)
    db.commit()
    db.refresh(task)
    return ok(serialize_task(task))


@router.get("/{task_id}")
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = ensure_task_view_permission(db, get_task_or_404(db, task_id), current_user)
    return ok(serialize_task(task, include_detail=True))


@router.put("/{task_id}")
def update_task(
    task_id: int,
    payload: TaskUpdatePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = ensure_task_view_permission(db, get_task_or_404(db, task_id), current_user)
    ensure_task_edit_permission(db, task, current_user)

    if "title" in payload.model_fields_set:
        validate_title(payload.title)
        task.title = payload.title.strip()
    if "description" in payload.model_fields_set:
        task.description = payload.description
    if "priority" in payload.model_fields_set:
        validate_priority(payload.priority)
        task.priority = payload.priority
    if "due_date" in payload.model_fields_set:
        task.due_date = payload.due_date
    if "start_date" in payload.model_fields_set:
        task.start_date = payload.start_date
    if "labels" in payload.model_fields_set:
        replace_labels(db, task, payload.labels or [])

    db.commit()
    db.refresh(task)
    return ok(serialize_task(task))


@router.patch("/{task_id}/status")
def update_task_status(
    task_id: int,
    payload: TaskStatusPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    validate_status(payload.status)
    task = ensure_task_view_permission(db, get_task_or_404(db, task_id), current_user)
    ensure_task_status_permission(db, task, current_user)
    task.status = payload.status
    db.commit()
    db.refresh(task)
    return ok(serialize_task(task))


@router.patch("/{task_id}/assignee")
def update_task_assignee(
    task_id: int,
    payload: TaskAssigneePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = ensure_task_view_permission(db, get_task_or_404(db, task_id), current_user)
    ensure_task_assignee_permission(db, task, current_user)
    task.assigned_to = validate_assignee(db, task.team_id, payload.assigned_to)
    db.commit()
    db.refresh(task)
    return ok(serialize_task(task))


@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = ensure_task_view_permission(db, get_task_or_404(db, task_id), current_user)
    ensure_task_delete_permission(db, task, current_user)
    db.delete(task)
    db.commit()
    return ok(None)
