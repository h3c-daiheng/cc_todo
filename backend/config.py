# backend/config.py
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

SECRET_KEY = os.environ.get("TODO_SECRET_KEY", "")
if not SECRET_KEY:
    SECRET_KEY = "dev-secret-key-change-in-prod"
    logger.warning("TODO_SECRET_KEY not set — using insecure default. Set this env var in production!")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480   # 8 小时
REFRESH_TOKEN_EXPIRE_DAYS = 7

UPLOAD_DIR = Path(os.environ.get("TODO_UPLOAD_DIR", "./uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_UPLOAD_SIZE = 20 * 1024 * 1024  # 20MB

ALLOWED_MIME_TYPES = {
    "image/jpeg", "image/png", "image/gif",
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}

DATABASE_URL = "sqlite:///./todo.db"

_BACKEND_DIR = Path(__file__).resolve().parent
ADMIN_CONFIG_PATH = Path(os.environ.get("TODO_ADMIN_CONFIG", str(_BACKEND_DIR / "admin.yaml")))
