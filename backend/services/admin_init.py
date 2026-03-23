# backend/services/admin_init.py
import logging
from pathlib import Path

import yaml
from sqlalchemy.exc import IntegrityError

from models import User
from services.auth import hash_password

logger = logging.getLogger(__name__)


def ensure_admins(db, config_path: str | Path | None = None):
    """Read admin.yaml and create any admin users that don't already exist."""
    if config_path is None:
        from config import ADMIN_CONFIG_PATH
        config_path = ADMIN_CONFIG_PATH

    path = Path(config_path)
    if not path.exists():
        logger.debug("Admin config %s not found, skipping.", path)
        return

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        logger.warning("Failed to parse admin config %s", path, exc_info=True)
        return

    admins = data.get("admins") or []
    for entry in admins:
        username = entry.get("username", "").strip()
        email = entry.get("email", "").strip()
        password = entry.get("password", "")

        if not username or not email or not password:
            logger.warning("Skipping admin entry with missing fields: %s", entry)
            continue

        if len(password) < 6:
            logger.warning("Skipping admin '%s': password must be at least 6 characters.", username)
            continue

        if db.query(User).filter(User.username == username).first():
            logger.info("Admin '%s' already exists, skipping.", username)
            continue

        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            is_admin=True,
        )
        db.add(user)
        try:
            db.commit()
            logger.info("Created admin account '%s'.", username)
        except IntegrityError:
            db.rollback()
            logger.warning("Skipping admin '%s': duplicate email or constraint violation.", username)
