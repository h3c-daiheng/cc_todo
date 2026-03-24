# Admin Account from Config File — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create admin accounts automatically on app startup by reading a YAML config file, replacing the interactive `init_admin.py` script.

**Architecture:** A `admin.yaml` config file defines admin credentials. On FastAPI startup, a new `ensure_admins()` function reads the file and upserts admin users (create if missing, skip if exists). The interactive script is removed.

**Tech Stack:** PyYAML for config parsing, existing SQLAlchemy models and bcrypt hashing.

---

## File Structure

| Action | Path | Responsibility |
|--------|------|---------------|
| Create | `backend/admin.yaml.example` | Sample config with placeholder credentials |
| Create | `backend/admin.yaml` | Actual config (gitignored) |
| Modify | `.gitignore` (project root) | Add `backend/admin.yaml` to prevent committing secrets |
| Modify | `backend/requirements.txt` | Add `pyyaml` |
| Create | `backend/services/admin_init.py` | `ensure_admins(db)` — reads YAML, creates missing admin users |
| Modify | `backend/main.py:8-20` | Call `ensure_admins()` during startup |
| Delete | `backend/scripts/init_admin.py` | No longer needed |
| Create | `backend/tests/test_admin_init.py` | Tests for `ensure_admins()` |
| Modify | `backend/config.py` | Add `ADMIN_CONFIG_PATH` constant |

---

### Task 1: Add PyYAML dependency

**Files:**
- Modify: `backend/requirements.txt`

- [ ] **Step 1: Add pyyaml to requirements.txt**

Add `pyyaml>=6.0` to `backend/requirements.txt`.

- [ ] **Step 2: Install**

Run: `cd /root/todo/backend && pip install pyyaml`

- [ ] **Step 3: Commit**

```bash
git add backend/requirements.txt
git commit -m "chore: add pyyaml dependency for admin config"
```

---

### Task 2: Create admin config file and gitignore

**Files:**
- Create: `backend/admin.yaml.example`
- Create: `backend/admin.yaml`
- Modify: `.gitignore` (project root)

- [ ] **Step 1: Create `admin.yaml.example`**

```yaml
# Admin accounts — created automatically on app startup.
# Copy this file to admin.yaml and edit credentials.
# Users that already exist (by username) are skipped.
admins:
  - username: admin
    email: admin@example.com
    password: changeme123
```

- [ ] **Step 2: Create `admin.yaml` with same content**

Copy from example so the app has a working default on first run.

- [ ] **Step 3: Add `backend/admin.yaml` to root `.gitignore`**

Add `backend/admin.yaml` to `/root/todo/.gitignore` so real credentials are never committed.

- [ ] **Step 4: Commit**

```bash
git add backend/admin.yaml.example .gitignore
git commit -m "chore: add admin config example and gitignore"
```

---

### Task 3: Add ADMIN_CONFIG_PATH to config.py

**Files:**
- Modify: `backend/config.py`

- [ ] **Step 1: Add config constant**

Add to `backend/config.py`:

```python
_BACKEND_DIR = Path(__file__).resolve().parent
ADMIN_CONFIG_PATH = Path(os.environ.get("TODO_ADMIN_CONFIG", str(_BACKEND_DIR / "admin.yaml")))
```

Anchored to `backend/` directory so it works regardless of the working directory. Override via `TODO_ADMIN_CONFIG` env var.

- [ ] **Step 2: Commit**

```bash
git add backend/config.py
git commit -m "feat: add ADMIN_CONFIG_PATH config constant"
```

---

### Task 4: Write failing tests for ensure_admins

**Files:**
- Create: `backend/tests/test_admin_init.py`

- [ ] **Step 1: Write tests**

```python
# backend/tests/test_admin_init.py
import os
import tempfile
import yaml
import pytest
from models import User
from services.admin_init import ensure_admins
from services.auth import verify_password


def write_config(path, data):
    with open(path, "w") as f:
        yaml.dump(data, f)


def test_creates_admin_from_config(db):
    """Admin user is created when config has a new admin entry."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump({"admins": [
            {"username": "cfgadmin", "email": "cfg@test.com", "password": "secret123"}
        ]}, f)
        path = f.name
    try:
        ensure_admins(db, config_path=path)
        user = db.query(User).filter(User.username == "cfgadmin").first()
        assert user is not None
        assert user.is_admin is True
        assert user.email == "cfg@test.com"
        assert verify_password("secret123", user.password_hash)
    finally:
        os.unlink(path)


def test_skips_existing_user(db):
    """Existing admin user is not overwritten."""
    from services.auth import hash_password
    existing = User(username="existing", email="old@test.com",
                    password_hash=hash_password("oldpass"), is_admin=True)
    db.add(existing)
    db.commit()

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump({"admins": [
            {"username": "existing", "email": "new@test.com", "password": "newpass"}
        ]}, f)
        path = f.name
    try:
        ensure_admins(db, config_path=path)
        user = db.query(User).filter(User.username == "existing").first()
        assert user.email == "old@test.com"  # unchanged
        assert verify_password("oldpass", user.password_hash)  # unchanged
    finally:
        os.unlink(path)


def test_missing_config_is_noop(db):
    """No error when config file does not exist."""
    ensure_admins(db, config_path="/nonexistent/admin.yaml")
    assert db.query(User).count() == 0


def test_empty_config_is_noop(db):
    """No error when config has no admins key."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump({}, f)
        path = f.name
    try:
        ensure_admins(db, config_path=path)
        assert db.query(User).count() == 0
    finally:
        os.unlink(path)


def test_multiple_admins(db):
    """Multiple admins can be created in one config."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump({"admins": [
            {"username": "admin1", "email": "a1@test.com", "password": "pass123"},
            {"username": "admin2", "email": "a2@test.com", "password": "pass456"},
        ]}, f)
        path = f.name
    try:
        ensure_admins(db, config_path=path)
        assert db.query(User).filter(User.is_admin == True).count() == 2
    finally:
        os.unlink(path)


def test_rejects_short_password(db):
    """Admin entry with password < 6 chars is skipped with warning."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump({"admins": [
            {"username": "weak", "email": "w@test.com", "password": "123"}
        ]}, f)
        path = f.name
    try:
        ensure_admins(db, config_path=path)
        assert db.query(User).filter(User.username == "weak").first() is None
    finally:
        os.unlink(path)


def test_skips_duplicate_email(db):
    """Admin with duplicate email is skipped gracefully (no crash)."""
    from services.auth import hash_password
    existing = User(username="alice", email="dup@test.com",
                    password_hash=hash_password("alice123"))
    db.add(existing)
    db.commit()

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump({"admins": [
            {"username": "newadmin", "email": "dup@test.com", "password": "secret123"}
        ]}, f)
        path = f.name
    try:
        ensure_admins(db, config_path=path)
        # Original user unchanged, no new user created
        assert db.query(User).filter(User.email == "dup@test.com").count() == 1
        assert db.query(User).filter(User.username == "alice").first() is not None
    finally:
        os.unlink(path)


def test_skips_entry_with_missing_fields(db):
    """Entries with missing username, email, or password are skipped."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump({"admins": [
            {"username": "", "email": "a@test.com", "password": "pass123"},
            {"username": "bob", "email": "", "password": "pass123"},
            {"username": "carol", "email": "c@test.com", "password": ""},
        ]}, f)
        path = f.name
    try:
        ensure_admins(db, config_path=path)
        assert db.query(User).count() == 0
    finally:
        os.unlink(path)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /root/todo/backend && python3 -m pytest tests/test_admin_init.py -v`
Expected: ImportError — `services.admin_init` does not exist yet.

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_admin_init.py
git commit -m "test: add failing tests for admin config initialization"
```

---

### Task 5: Implement ensure_admins service

**Files:**
- Create: `backend/services/admin_init.py`

- [ ] **Step 1: Implement**

```python
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
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `cd /root/todo/backend && python3 -m pytest tests/test_admin_init.py -v`
Expected: All 8 tests PASS.

- [ ] **Step 3: Commit**

```bash
git add backend/services/admin_init.py
git commit -m "feat: implement ensure_admins to create admins from YAML config"
```

---

### Task 6: Wire ensure_admins into app startup

**Files:**
- Modify: `backend/main.py:8-20`

- [ ] **Step 1: Add ensure_admins call to startup**

In `backend/main.py`, inside the `startup()` function, add after `create_tables()`:

```python
from services.admin_init import ensure_admins
db = SessionLocal()
try:
    ensure_admins(db)
finally:
    db.close()
```

The full startup function becomes:

```python
@app.on_event("startup")
def startup():
    create_tables()

    from database import SessionLocal
    from services.admin_init import ensure_admins

    db = SessionLocal()
    try:
        ensure_admins(db)

        from models import SystemSetting
        row = db.get(SystemSetting, "email_send_hour")
        hour = int(row.value) if row and row.value else 8
    finally:
        db.close()

    from scheduler import start_scheduler
    start_scheduler(hour)
```

- [ ] **Step 2: Run all tests to verify no regressions**

Run: `cd /root/todo/backend && python3 -m pytest tests/ -v`
Expected: All tests PASS.

- [ ] **Step 3: Commit**

```bash
git add backend/main.py
git commit -m "feat: call ensure_admins on app startup"
```

---

### Task 7: Remove old init_admin.py script

**Files:**
- Delete: `backend/scripts/init_admin.py`

- [ ] **Step 1: Delete the script**

```bash
rm backend/scripts/init_admin.py
```

If `backend/scripts/` is now empty, remove the directory too.

- [ ] **Step 2: Commit**

```bash
git add -u backend/scripts/
git commit -m "chore: remove interactive init_admin.py, replaced by admin.yaml config"
```

---

### Task 8: Update CLAUDE.md

**Files:**
- Modify: `/root/todo/CLAUDE.md`

- [ ] **Step 1: Update admin creation command**

Replace:
```
cd backend && python3 scripts/init_admin.py --username admin --email admin@example.com  # Create admin
```

With:
```
cp backend/admin.yaml.example backend/admin.yaml   # Edit admin credentials, then start the app
```

- [ ] **Step 2: Add note in Important Details section**

Add to the Important Details list:
```
- Admin accounts: defined in `backend/admin.yaml` (gitignored), auto-created on startup if user doesn't exist. Copy from `admin.yaml.example`.
```

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md for admin config file approach"
```
