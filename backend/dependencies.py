# backend/dependencies.py
from collections import defaultdict
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from database import get_db
from models import Task, Team, TeamMember, User
from services.auth import decode_token

bearer = HTTPBearer(auto_error=False)

# In-memory blacklist for revoked refresh tokens
_blacklist: set[str] = set()

# Brute-force protection: {ip: [(timestamp, success), ...]}
_login_attempts: dict[str, list] = defaultdict(list)

# Registration rate limiting (separate from login)
_register_attempts: dict[str, list] = defaultdict(list)


def blacklist_token(token: str):
    _blacklist.add(token)


def is_blacklisted(token: str) -> bool:
    return token in _blacklist


def record_login_attempt(ip: str, success: bool):
    now = datetime.now(timezone.utc).timestamp()
    _login_attempts[ip] = [a for a in _login_attempts[ip] if now - a[0] < 300] + [(now, success)]


def is_ip_locked(ip: str) -> bool:
    now = datetime.now(timezone.utc).timestamp()
    recent_failures = [a for a in _login_attempts[ip] if now - a[0] < 300 and not a[1]]
    if len(recent_failures) >= 10:
        last_fail = max(a[0] for a in recent_failures)
        return (now - last_fail) < 900
    return False


def record_register_attempt(ip: str, success: bool):
    now = datetime.now(timezone.utc).timestamp()
    _register_attempts[ip] = [a for a in _register_attempts[ip] if now - a[0] < 300] + [(now, success)]


def is_register_locked(ip: str) -> bool:
    now = datetime.now(timezone.utc).timestamp()
    recent_failures = [a for a in _register_attempts[ip] if now - a[0] < 300 and not a[1]]
    if len(recent_failures) >= 10:
        last_fail = max(a[0] for a in recent_failures)
        return (now - last_fail) < 900
    return False


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token 无效或已过期")
    user_id = payload.get("sub")
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token 无效或已过期")
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="账号不存在或已停用")
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    return current_user


def is_team_member(db: Session, team_id: int, user_id: int) -> bool:
    return (
        db.query(TeamMember)
        .filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
        .first()
        is not None
    )


def is_task_team_leader(db: Session, task: Task, user: User) -> bool:
    if not task.team_id:
        return False
    team = db.get(Team, task.team_id)
    return bool(team and team.created_by == user.id)


def ensure_task_view_permission(db: Session, task: Task, user: User) -> Task:
    if user.is_admin or task.created_by == user.id or task.assigned_to == user.id:
        return task
    if task.team_id and is_team_member(db, task.team_id, user.id):
        return task
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看该任务")


def ensure_task_edit_permission(db: Session, task: Task, user: User) -> Task:
    if user.is_admin or task.created_by == user.id or is_task_team_leader(db, task, user):
        return task
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权编辑该任务")


def ensure_task_status_permission(db: Session, task: Task, user: User) -> Task:
    if (
        user.is_admin
        or task.created_by == user.id
        or task.assigned_to == user.id
        or is_task_team_leader(db, task, user)
    ):
        return task
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权修改任务状态")


def ensure_task_assignee_permission(db: Session, task: Task, user: User) -> Task:
    if user.is_admin or task.created_by == user.id or is_task_team_leader(db, task, user):
        return task
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权分配任务负责人")


def ensure_task_delete_permission(db: Session, task: Task, user: User) -> Task:
    if user.is_admin or task.created_by == user.id or is_task_team_leader(db, task, user):
        return task
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权删除该任务")
