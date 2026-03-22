# backend/tests/test_auth.py
def test_login_success(client, normal_user):
    resp = client.post("/api/v1/auth/login", json={"username": "alice", "password": "alice123"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "access_token" in data

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
