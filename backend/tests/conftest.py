# backend/tests/conftest.py
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from database import Base, get_db
from main import app
from models import User
from services.auth import hash_password

TEST_DB_URL = "sqlite://"
test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

@event.listens_for(test_engine, "connect")
def set_pragmas(dbapi_conn, _):
    dbapi_conn.execute("PRAGMA journal_mode=WAL")
    dbapi_conn.execute("PRAGMA foreign_keys=ON")

TestingSession = sessionmaker(bind=test_engine)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def db():
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def client(db):
    def override_db():
        yield db
    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def admin_user(db):
    user = User(
        username="admin", email="admin@test.com",
        password_hash=hash_password("admin123"), is_admin=True
    )
    db.add(user); db.commit(); db.refresh(user)
    return user

@pytest.fixture
def normal_user(db):
    user = User(
        username="alice", email="alice@test.com",
        password_hash=hash_password("alice123")
    )
    db.add(user); db.commit(); db.refresh(user)
    return user

@pytest.fixture
def auth_headers(client, normal_user):
    resp = client.post("/api/v1/auth/login", json={"username": "alice", "password": "alice123"})
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def admin_headers(client, admin_user):
    resp = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
