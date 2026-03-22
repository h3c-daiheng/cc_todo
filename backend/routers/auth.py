# backend/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from models import User
from services.auth import verify_password, create_access_token, create_refresh_token, decode_token
from dependencies import (
    blacklist_token, is_blacklisted, record_login_attempt,
    is_ip_locked, get_current_user
)

router = APIRouter(prefix="/auth", tags=["auth"])

def ok(data):
    return {"code": 0, "message": "ok", "data": data}

class LoginRequest(BaseModel):
    username: str
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
    return ok({"access_token": access_token, "token_type": "bearer"})

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
