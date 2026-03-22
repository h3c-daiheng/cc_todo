from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from dependencies import require_admin
from models import User
from services.auth import hash_password

router = APIRouter(prefix="/users", tags=["users"])


def ok(data):
    return {"code": 0, "message": "ok", "data": data}


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    is_admin: bool = False


class UserUpdatePayload(BaseModel):
    email: str | None = None
    is_active: bool | None = None
    is_admin: bool | None = None
    email_notify: bool | None = None
    password: str | None = None



def serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_admin": user.is_admin,
        "is_active": user.is_active,
        "email_notify": user.email_notify,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


@router.get("")
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    users = db.query(User).order_by(User.id.asc()).all()
    return ok([serialize_user(user) for user in users])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="用户名已存在")
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="邮箱已被使用")
    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
        is_admin=payload.is_admin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return ok(serialize_user(user))


@router.put("/{user_id}")
def update_user(
    user_id: int,
    payload: UserUpdatePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    if "email" in payload.model_fields_set:
        user.email = payload.email
    if "is_active" in payload.model_fields_set:
        user.is_active = payload.is_active
    if "is_admin" in payload.model_fields_set:
        user.is_admin = payload.is_admin
    if "email_notify" in payload.model_fields_set:
        user.email_notify = payload.email_notify
    if "password" in payload.model_fields_set and payload.password:
        user.password_hash = hash_password(payload.password)

    db.commit()
    db.refresh(user)
    return ok(serialize_user(user))
