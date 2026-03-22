from models import SystemSetting, User
from services.auth import hash_password


def create_user(db, username: str, email: str, password: str, is_admin: bool = False, is_active: bool = True):
    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        is_admin=is_admin,
        is_active=is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_admin_can_list_users(client, admin_headers, normal_user, db):
    create_user(db, "bob", "bob@test.com", "bob123", is_active=False)

    response = client.get("/api/v1/users", headers=admin_headers)

    assert response.status_code == 200
    items = response.json()["data"]
    assert [item["username"] for item in items] == ["admin", "alice", "bob"]
    assert items[2]["is_active"] is False



def test_non_admin_cannot_list_users(client, auth_headers):
    response = client.get("/api/v1/users", headers=auth_headers)

    assert response.status_code == 403
    assert response.json()["detail"] == "需要管理员权限"



def test_admin_can_update_user_status_and_admin_flag(client, admin_headers, normal_user):
    response = client.put(
        f"/api/v1/users/{normal_user.id}",
        json={"is_active": False, "is_admin": True, "email_notify": False},
        headers=admin_headers,
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["id"] == normal_user.id
    assert data["is_active"] is False
    assert data["is_admin"] is True
    assert data["email_notify"] is False



def test_admin_can_get_and_update_system_settings(client, admin_headers, db, monkeypatch):
    calls = []
    monkeypatch.setattr("routers.settings.reschedule_email_job", lambda hour: calls.append(hour))

    response = client.get("/api/v1/settings", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["data"]["email_send_hour"] == 8

    update_response = client.put(
        "/api/v1/settings",
        json={
            "smtp_host": "smtp.example.com",
            "smtp_port": 587,
            "smtp_username": "bot",
            "smtp_password": "secret",
            "smtp_from": "bot@example.com",
            "smtp_use_tls": True,
            "email_send_hour": 9,
        },
        headers=admin_headers,
    )

    assert update_response.status_code == 200
    data = update_response.json()["data"]
    assert data["smtp_host"] == "smtp.example.com"
    assert data["smtp_port"] == 587
    assert data["smtp_username"] == "bot"
    assert data["smtp_password"] == "secret"
    assert data["smtp_from"] == "bot@example.com"
    assert data["smtp_use_tls"] is True
    assert data["email_send_hour"] == 9
    assert calls == [9]

    rows = db.query(SystemSetting).order_by(SystemSetting.key.asc()).all()
    assert {row.key: row.value for row in rows}["email_send_hour"] == "9"



def test_settings_reject_invalid_email_send_hour(client, admin_headers):
    response = client.put(
        "/api/v1/settings",
        json={"email_send_hour": 24},
        headers=admin_headers,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "发送小时必须在 0-23 之间"
