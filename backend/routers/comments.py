from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from dependencies import ensure_task_view_permission, get_current_user
from models import Comment, Task, User

router = APIRouter(tags=["comments"])


def ok(data):
    return {"code": 0, "message": "ok", "data": data}


class CommentCreate(BaseModel):
    content: str


def get_task_or_404(db: Session, task_id: int) -> Task:
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")
    return task


def get_comment_or_404(db: Session, comment_id: int) -> Comment:
    comment = db.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="评论不存在")
    return comment


@router.post("/tasks/{task_id}/comments")
def add_comment(
    task_id: int,
    payload: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not payload.content or not payload.content.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="评论内容不能为空")

    task = get_task_or_404(db, task_id)
    ensure_task_view_permission(db, task, current_user)

    comment = Comment(
        task_id=task_id,
        user_id=current_user.id,
        content=payload.content.strip(),
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    return ok({
        "id": comment.id,
        "content": comment.content,
        "user_id": comment.user_id,
        "created_at": comment.created_at.isoformat() if comment.created_at else None,
    })


@router.delete("/comments/{comment_id}")
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    comment = get_comment_or_404(db, comment_id)

    if not current_user.is_admin and comment.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权删除该评论")

    db.delete(comment)
    db.commit()
    return ok(None)
