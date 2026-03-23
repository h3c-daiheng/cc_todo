# backend/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
import re
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from database import get_db
from models import User, SystemSetting
from services.auth import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from dependencies import (
    blacklist_token, is_blacklisted, record_login_attempt,
    is_ip_locked, get_current_user,
    record_register_attempt, is_register_locked,
)

router = APIRouter(prefix="/auth", tags=["auth"])

def ok(data):
    return {"code": 0, "message": "ok", "data": data}

USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{2,64}$")

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

@router.post("/login")
def login(req: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "unknown"
    if is_ip_locked(ip):
        raise HTTPException(status_code=429, detail="登录尝试过于频繁，请 15 分钟后再试")
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not user.is_active or not verify_password(req.password, user.password_hash):
        record_login_attempt(ip, False)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    record_login_attempt(ip, True)
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id), "type": "refresh"})
    response.set_cookie("refresh_token", refresh_token, httponly=True, max_age=7 * 86400)
    return ok({"access_token": access_token, "token_type": "bearer", "is_admin": user.is_admin})

@router.post("/register")
def register(req: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    # Check registration switch
    setting = db.get(SystemSetting, "allow_registration")
    if setting and setting.value == "false":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="系统已关闭注册")
    # Rate limiting
    ip = request.client.host if request.client else "unknown"
    if is_register_locked(ip):
        raise HTTPException(status_code=429, detail="注册尝试过于频繁，请 15 分钟后再试")
    # Validate username format
    if not USERNAME_RE.match(req.username):
        record_register_attempt(ip, False)
        raise HTTPException(status_code=400, detail="用户名须为 2-64 位字母、数字或下划线")
    # Validate password length
    if len(req.password) < 6:
        record_register_attempt(ip, False)
        raise HTTPException(status_code=400, detail="密码至少需要 6 位")
    # Check uniqueness
    if db.query(User).filter(User.username == req.username).first():
        record_register_attempt(ip, False)
        raise HTTPException(status_code=400, detail="用户名已存在")
    if db.query(User).filter(User.email == req.email).first():
        record_register_attempt(ip, False)
        raise HTTPException(status_code=400, detail="邮箱已存在")
    # Create user
    user = User(
        username=req.username, email=req.email,
        password_hash=hash_password(req.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    record_register_attempt(ip, True)
    return ok({"id": user.id, "username": user.username, "email": user.email})

@router.post("/logout")
def logout(response: Response, current_user: User = Depends(get_current_user)):
    response.delete_cookie("refresh_token")
    return ok(None)

@router.post("/refresh")
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get("refresh_token")
    if not token or is_blacklisted(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="refresh token 无效")
    payload = decode_token(token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="refresh token 无效")
    user = db.get(User, int(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="账号不存在或已停用")
    new_access = create_access_token({"sub": str(user.id)})
    return ok({"access_token": new_access})
