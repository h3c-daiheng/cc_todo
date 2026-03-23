from datetime import date

from models import Task, TaskLabel, Team, TeamMember, User
from services.auth import create_access_token, hash_password


def create_user(db, username: str, email: str, password: str, is_admin: bool = False):
    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        is_admin=is_admin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_team(db, name: str, leader_id: int):
    team = Team(name=name, created_by=leader_id)
    db.add(team)
    db.flush()
    db.add(TeamMember(team_id=team.id, user_id=leader_id))
    db.commit()
    db.refresh(team)
    return team


def make_headers(user_id: int):
    token = create_access_token({"sub": str(user_id)})
    return {"Authorization": f"Bearer {token}"}


def test_create_personal_task(client, auth_headers):
    response = client.post(
        "/api/v1/tasks",
        json={"title": "买菜", "priority": "high", "labels": ["生活", "紧急"]},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["title"] == "买菜"
    assert data["team_id"] is None
    assert data["labels"] == ["生活", "紧急"]


def test_list_returns_own_tasks_and_supports_due_date_filter(client, auth_headers, normal_user, db):
    other = create_user(db, "bob", "bob@test.com", "bob123")
    db.add(
        Task(
            title="别人的任务",
            description="desc",
            status="pending",
            priority="medium",
            due_date=date(2026, 3, 23),
            created_by=other.id,
        )
    )
    db.commit()

    client.post(
        "/api/v1/tasks",
        json={"title": "今天任务", "due_date": "2026-03-23"},
        headers=auth_headers,
    )
    client.post(
        "/api/v1/tasks",
        json={"title": "明天任务", "due_date": "2026-03-24"},
        headers=auth_headers,
    )

    response = client.get("/api/v1/tasks?due_date=2026-03-23", headers=auth_headers)

    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["title"] == "今天任务"
    assert items[0]["created_by"] == normal_user.id


def test_update_task_status(client, auth_headers):
    created = client.post("/api/v1/tasks", json={"title": "任务"}, headers=auth_headers)
    assert created.status_code == 200
    task_id = created.json()["data"]["id"]

    response = client.patch(
        f"/api/v1/tasks/{task_id}/status",
        json={"status": "in_progress"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "in_progress"


def test_delete_task(client, auth_headers, db):
    created = client.post("/api/v1/tasks", json={"title": "临时任务"}, headers=auth_headers)
    assert created.status_code == 200
    task_id = created.json()["data"]["id"]

    response = client.delete(f"/api/v1/tasks/{task_id}", headers=auth_headers)

    assert response.status_code == 200
    assert db.get(Task, task_id) is None


def test_other_user_cannot_delete_personal_task(client, auth_headers, db):
    other = create_user(db, "bob2", "bob2@test.com", "bob123")
    created = client.post("/api/v1/tasks", json={"title": "Alice任务"}, headers=auth_headers)
    assert created.status_code == 200
    task_id = created.json()["data"]["id"]

    response = client.delete(f"/api/v1/tasks/{task_id}", headers=make_headers(other.id))

    assert response.status_code == 403
    assert response.json()["detail"] == "无权查看该任务"


def test_team_member_can_view_team_task(client, auth_headers, normal_user, db):
    owner = create_user(db, "owner", "owner@test.com", "owner123")
    team = create_team(db, "研发组", owner.id)
    db.add(TeamMember(team_id=team.id, user_id=normal_user.id))
    db.commit()

    task = Task(
        title="团队任务",
        description="desc",
        status="pending",
        priority="medium",
        due_date=date(2026, 3, 23),
        created_by=owner.id,
        assigned_to=None,
        team_id=team.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    response = client.get(f"/api/v1/tasks/{task.id}", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["data"]["id"] == task.id


def test_team_member_can_view_but_cannot_edit_team_task(client, auth_headers, normal_user, db):
    owner = create_user(db, "owner_edit", "owner_edit@test.com", "owneredit123")
    team = create_team(db, "协作组", owner.id)
    db.add(TeamMember(team_id=team.id, user_id=normal_user.id))
    db.commit()

    task = Task(
        title="协作任务",
        description="desc",
        status="pending",
        priority="medium",
        due_date=date(2026, 3, 23),
        created_by=owner.id,
        team_id=team.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    response = client.put(
        f"/api/v1/tasks/{task.id}",
        json={"title": "改标题"},
        headers=auth_headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "无权编辑该任务"


def test_non_member_cannot_view_team_task(client, auth_headers, db):
    owner = create_user(db, "owner2", "owner2@test.com", "owner2123")
    team = create_team(db, "保密组", owner.id)
    task = Task(
        title="保密任务",
        description="desc",
        status="pending",
        priority="medium",
        due_date=date(2026, 3, 23),
        created_by=owner.id,
        team_id=team.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    response = client.get(f"/api/v1/tasks/{task.id}", headers=auth_headers)

    assert response.status_code == 403
    assert response.json()["detail"] == "无权查看该任务"


def test_team_leader_can_edit_and_delete_team_task(client, auth_headers, normal_user, db):
    member = create_user(db, "member", "member@test.com", "member123")
    team = create_team(db, "产品组", normal_user.id)
    db.add(TeamMember(team_id=team.id, user_id=member.id))
    db.commit()

    task = Task(
        title="旧标题",
        description="旧描述",
        status="pending",
        priority="medium",
        due_date=date(2026, 3, 23),
        created_by=member.id,
        team_id=team.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    update_response = client.put(
        f"/api/v1/tasks/{task.id}",
        json={"title": "新标题", "description": "新描述", "labels": ["团队"]},
        headers=auth_headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["title"] == "新标题"
    assert update_response.json()["data"]["labels"] == ["团队"]

    delete_response = client.delete(f"/api/v1/tasks/{task.id}", headers=auth_headers)
    assert delete_response.status_code == 200
    assert db.get(Task, task.id) is None


def test_assignee_permission_and_team_member_validation(client, auth_headers, normal_user, db):
    teammate = create_user(db, "teammate", "teammate@test.com", "teammate123")
    outsider = create_user(db, "outsider", "outsider@test.com", "outsider123")
    team = create_team(db, "测试组", normal_user.id)
    db.add(TeamMember(team_id=team.id, user_id=teammate.id))
    db.commit()

    created = client.post(
        "/api/v1/tasks",
        json={"title": "团队任务", "team_id": team.id},
        headers=auth_headers,
    )
    assert created.status_code == 200
    task_id = created.json()["data"]["id"]

    invalid_response = client.patch(
        f"/api/v1/tasks/{task_id}/assignee",
        json={"assigned_to": outsider.id},
        headers=auth_headers,
    )
    assert invalid_response.status_code == 400
    assert invalid_response.json()["detail"] == "团队任务负责人必须是团队成员"

    valid_response = client.patch(
        f"/api/v1/tasks/{task_id}/assignee",
        json={"assigned_to": teammate.id},
        headers=auth_headers,
    )
    assert valid_response.status_code == 200
    assert valid_response.json()["data"]["assigned_to"] == teammate.id

    non_owner = create_user(db, "eve", "eve@test.com", "eve123")
    forbidden_response = client.patch(
        f"/api/v1/tasks/{task_id}/assignee",
        json={"assigned_to": normal_user.id},
        headers=make_headers(non_owner.id),
    )
    assert forbidden_response.status_code == 403
    assert forbidden_response.json()["detail"] == "无权查看该任务"


def test_labels_can_be_written_and_read(client, auth_headers, db):
    created = client.post(
        "/api/v1/tasks",
        json={"title": "标签任务", "labels": ["A", "B", "A", " "]},
        headers=auth_headers,
    )
    assert created.status_code == 200
    task_id = created.json()["data"]["id"]
    assert created.json()["data"]["labels"] == ["A", "B"]

    response = client.put(
        f"/api/v1/tasks/{task_id}",
        json={"labels": ["C", "D"]},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["data"]["labels"] == ["C", "D"]
    labels = db.query(TaskLabel).filter(TaskLabel.task_id == task_id).order_by(TaskLabel.label.asc()).all()
    assert [item.label for item in labels] == ["C", "D"]


def test_update_task_rejects_null_title(client, auth_headers):
    created = client.post("/api/v1/tasks", json={"title": "原任务"}, headers=auth_headers)
    assert created.status_code == 200
    task_id = created.json()["data"]["id"]

    response = client.put(
        f"/api/v1/tasks/{task_id}",
        json={"title": None},
        headers=auth_headers,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "标题不能为空"


def test_create_task_with_start_date(client, auth_headers):
    response = client.post(
        "/api/v1/tasks",
        json={"title": "有开始日期", "start_date": "2026-03-20", "due_date": "2026-03-30"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["start_date"] == "2026-03-20"
    assert data["due_date"] == "2026-03-30"


def test_update_task_start_date(client, auth_headers):
    created = client.post("/api/v1/tasks", json={"title": "任务"}, headers=auth_headers)
    task_id = created.json()["data"]["id"]

    response = client.put(
        f"/api/v1/tasks/{task_id}",
        json={"start_date": "2026-04-01"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["start_date"] == "2026-04-01"


def test_start_date_defaults_to_null(client, auth_headers):
    created = client.post("/api/v1/tasks", json={"title": "无日期任务"}, headers=auth_headers)
    assert created.status_code == 200
    assert created.json()["data"]["start_date"] is None


def test_list_tasks_filter_by_team_id(client, auth_headers, normal_user, db):
    """Team member can filter tasks by team_id and gets only that team's tasks."""
    other = create_user(db, "leader_t2", "leader_t2@test.com", "pass")
    team = create_team(db, "过滤测试组", other.id)
    db.add(TeamMember(team_id=team.id, user_id=normal_user.id))
    db.commit()

    client.post(
        "/api/v1/tasks",
        json={"title": "团队任务A", "team_id": team.id},
        headers=auth_headers,
    )
    client.post("/api/v1/tasks", json={"title": "个人任务"}, headers=auth_headers)

    response = client.get(f"/api/v1/tasks?team_id={team.id}", headers=auth_headers)
    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert all(t["team_id"] == team.id for t in items)
    assert any(t["title"] == "团队任务A" for t in items)


def test_list_tasks_team_id_filter_rejects_non_member(client, db):
    """Non-member gets 403 when filtering by a team they don't belong to."""
    outsider = create_user(db, "outsider_t2", "outsider_t2@test.com", "pass")
    leader = create_user(db, "leader_t3", "leader_t3@test.com", "pass")
    team = create_team(db, "私密组", leader.id)

    response = client.get(
        f"/api/v1/tasks?team_id={team.id}",
        headers=make_headers(outsider.id),
    )
    assert response.status_code == 403
