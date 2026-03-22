# backend/tests/test_models.py
import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from database import Base
import models  # noqa: ensure all models are registered

@pytest.fixture
def engine():
    e = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=e)
    yield e
    Base.metadata.drop_all(bind=e)

def test_all_tables_created(engine):
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    expected = {"users", "teams", "team_members", "tasks", "task_labels", "comments", "attachments", "system_settings"}
    assert expected.issubset(set(tables))

def test_user_model_columns(engine):
    inspector = inspect(engine)
    cols = {c["name"] for c in inspector.get_columns("users")}
    assert {"id", "username", "password_hash", "email", "is_admin", "email_notify", "is_active", "created_at"}.issubset(cols)

def test_task_labels_composite_pk(engine):
    Session = sessionmaker(bind=engine)
    db = Session()
    from models import User, Task, TaskLabel
    from datetime import datetime
    u = User(username="u", password_hash="h", email="u@t.com")
    db.add(u); db.flush()
    t = Task(title="T", created_by=u.id)
    db.add(t); db.flush()
    db.add(TaskLabel(task_id=t.id, label="bug"))
    db.commit()
    # Duplicate label should fail
    db.add(TaskLabel(task_id=t.id, label="bug"))
    with pytest.raises(Exception):
        db.commit()
    db.close()
