from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from dependencies import require_admin
from models import SystemSetting, User
from scheduler import reschedule_email_job

router = APIRouter(prefix="/settings", tags=["settings"])

DEFAULT_SETTINGS = {
    "smtp_host": "",
    "smtp_port": 25,
    "smtp_username": "",
    "smtp_password": "",
    "smtp_from": "",
    "smtp_use_tls": False,
    "email_send_hour": 8,
    "allow_registration": True,
}


def ok(data):
    return {"code": 0, "message": "ok", "data": data}


class SettingsPayload(BaseModel):
    smtp_host: str | None = None
    smtp_port: int | None = None
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
    smtp_use_tls: bool | None = None
    email_send_hour: int | None = None
    allow_registration: bool | None = None



def parse_setting_value(key: str, value: str | None):
    if value is None:
        return None
    if key in {"smtp_port", "email_send_hour"}:
        return int(value)
    if key in {"smtp_use_tls", "allow_registration"}:
        return value == "true"
    return value



def get_settings_dict(db: Session) -> dict:
    rows = db.query(SystemSetting).all()
    data = DEFAULT_SETTINGS.copy()
    for row in rows:
        data[row.key] = parse_setting_value(row.key, row.value)
    return data



def save_setting(db: Session, key: str, value):
    row = db.get(SystemSetting, key)
    stored_value = None
    if value is not None:
        if isinstance(value, bool):
            stored_value = "true" if value else "false"
        else:
            stored_value = str(value)
    if row:
        row.value = stored_value
    else:
        db.add(SystemSetting(key=key, value=stored_value))


@router.get("")
def get_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return ok(get_settings_dict(db))


@router.put("")
def update_settings(
    payload: SettingsPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    if payload.email_send_hour is not None and not 0 <= payload.email_send_hour <= 23:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="发送小时必须在 0-23 之间")

    changed_keys = payload.model_fields_set
    for key in changed_keys:
        save_setting(db, key, getattr(payload, key))

    db.commit()

    if "email_send_hour" in changed_keys and payload.email_send_hour is not None:
        reschedule_email_job(payload.email_send_hour)

    return ok(get_settings_dict(db))
