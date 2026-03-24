# backend/tests/test_auth.py
def test_login_success(client, normal_user):
    resp = client.post("/api/v1/auth/login", json={"username": "alice", "password": "alice123"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "access_token" in data
    assert data["is_admin"] is False

def test_login_wrong_password(client, normal_user):
    resp = client.post("/api/v1/auth/login", json={"username": "alice", "password": "wrong"})
    assert resp.status_code == 401

def test_login_inactive_user(client, db, normal_user):
    normal_user.is_active = False
    db.commit()
    resp = client.post("/api/v1/auth/login", json={"username": "alice", "password": "alice123"})
    assert resp.status_code == 401

def test_logout(client, auth_headers):
    resp = client.post("/api/v1/auth/logout", headers=auth_headers)
    assert resp.status_code == 200

def test_protected_route_requires_token(client, normal_user):
    resp = client.get("/api/v1/tasks")
    assert resp.status_code == 401


# --- Registration tests ---

def test_register_success(client):
    resp = client.post("/api/v1/auth/register", json={
        "username": "newuser", "email": "new@test.com", "password": "pass123"
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["username"] == "newuser"
    assert data["email"] == "new@test.com"
    assert "id" in data

def test_register_duplicate_username(client, normal_user):
    resp = client.post("/api/v1/auth/register", json={
        "username": "alice", "email": "other@test.com", "password": "pass123"
    })
    assert resp.status_code == 400
    assert "用户名已存在" in resp.json()["detail"]

def test_register_duplicate_email(client, normal_user):
    resp = client.post("/api/v1/auth/register", json={
        "username": "newuser2", "email": "alice@test.com", "password": "pass123"
    })
    assert resp.status_code == 400
    assert "邮箱已存在" in resp.json()["detail"]

def test_register_password_too_short(client):
    resp = client.post("/api/v1/auth/register", json={
        "username": "newuser3", "email": "short@test.com", "password": "abc"
    })
    assert resp.status_code == 400
    assert "密码至少需要 6 位" in resp.json()["detail"]

def test_register_invalid_username(client):
    resp = client.post("/api/v1/auth/register", json={
        "username": "a", "email": "bad@test.com", "password": "pass123"
    })
    assert resp.status_code == 400
    assert "用户名须为" in resp.json()["detail"]
    # Special characters
    resp2 = client.post("/api/v1/auth/register", json={
        "username": "user@name", "email": "bad2@test.com", "password": "pass123"
    })
    assert resp2.status_code == 400

def test_register_disabled(client, db):
    from models import SystemSetting
    db.add(SystemSetting(key="allow_registration", value="false"))
    db.commit()
    resp = client.post("/api/v1/auth/register", json={
        "username": "blocked", "email": "blocked@test.com", "password": "pass123"
    })
    assert resp.status_code == 403
    assert "系统已关闭注册" in resp.json()["detail"]
