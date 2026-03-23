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
