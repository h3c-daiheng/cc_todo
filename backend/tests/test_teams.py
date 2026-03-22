from datetime import date

from models import Team, TeamMember, User, Task
from services.auth import hash_password


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


def test_create_team(client, auth_headers, normal_user, db):
    response = client.post(
        "/api/v1/teams",
        json={"name": "研发组", "leader_id": normal_user.id},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["name"] == "研发组"
    assert data["leader_id"] == normal_user.id

    member = db.query(TeamMember).filter_by(team_id=data["id"], user_id=normal_user.id).first()
    assert member is not None


def test_list_teams_only_returns_accessible_teams(client, auth_headers, normal_user, db):
    own_team = create_team(db, "我的团队", normal_user.id)
    outsider = create_user(db, "bob", "bob@test.com", "bob123")
    create_team(db, "别人的团队", outsider.id)
    shared_team = create_team(db, "共享团队", outsider.id)
    db.add(TeamMember(team_id=shared_team.id, user_id=normal_user.id))
    db.commit()

    response = client.get("/api/v1/teams", headers=auth_headers)

    assert response.status_code == 200
    names = {item["name"] for item in response.json()["data"]}
    assert "我的团队" in names
    assert "共享团队" in names
    assert "别人的团队" not in names


def test_add_and_remove_team_member(client, auth_headers, normal_user, db):
    team = create_team(db, "产品组", normal_user.id)
    member = create_user(db, "carol", "carol@test.com", "carol123")

    add_response = client.post(
        f"/api/v1/teams/{team.id}/members",
        json={"user_id": member.id},
        headers=auth_headers,
    )
    assert add_response.status_code == 200
    assert add_response.json()["data"]["user_id"] == member.id

    list_response = client.get(f"/api/v1/teams/{team.id}/members", headers=auth_headers)
    member_ids = {item["user_id"] for item in list_response.json()["data"]}
    assert normal_user.id in member_ids
    assert member.id in member_ids

    remove_response = client.delete(
        f"/api/v1/teams/{team.id}/members/{member.id}",
        headers=auth_headers,
    )
    assert remove_response.status_code == 200
    assert db.query(TeamMember).filter_by(team_id=team.id, user_id=member.id).first() is None


def test_forbid_non_owner_modifying_team(client, auth_headers, db):
    owner = create_user(db, "owner", "owner@test.com", "owner123")
    team = create_team(db, "运营组", owner.id)

    response = client.post(
        f"/api/v1/teams/{team.id}/members",
        json={"user_id": owner.id},
        headers=auth_headers,
    )

    assert response.status_code == 403


def test_admin_can_manage_any_team(client, admin_headers, db):
    owner = create_user(db, "dave", "dave@test.com", "dave123")
    member = create_user(db, "erin", "erin@test.com", "erin123")
    team = create_team(db, "行政组", owner.id)

    response = client.post(
        f"/api/v1/teams/{team.id}/members",
        json={"user_id": member.id},
        headers=admin_headers,
    )

    assert response.status_code == 200
    assert db.query(TeamMember).filter_by(team_id=team.id, user_id=member.id).first() is not None


def test_member_can_view_team_but_cannot_modify(client, auth_headers, normal_user, db):
    owner = create_user(db, "frank", "frank@test.com", "frank123")
    team = create_team(db, "测试组", owner.id)
    db.add(TeamMember(team_id=team.id, user_id=normal_user.id))
    db.commit()

    detail_response = client.get(f"/api/v1/teams/{team.id}", headers=auth_headers)
    assert detail_response.status_code == 200
    assert detail_response.json()["data"]["id"] == team.id

    members_response = client.get(f"/api/v1/teams/{team.id}/members", headers=auth_headers)
    assert members_response.status_code == 200

    modify_response = client.put(
        f"/api/v1/teams/{team.id}",
        json={"name": "新名称", "leader_id": owner.id},
        headers=auth_headers,
    )
    assert modify_response.status_code == 403


def test_non_member_cannot_view_team(client, auth_headers, db):
    owner = create_user(db, "gina", "gina@test.com", "gina123")
    team = create_team(db, "保密组", owner.id)

    response = client.get(f"/api/v1/teams/{team.id}", headers=auth_headers)

    assert response.status_code == 403


def test_update_team_leader_auto_adds_membership(client, auth_headers, normal_user, db):
    team = create_team(db, "变更组", normal_user.id)
    new_leader = create_user(db, "henry", "henry@test.com", "henry123")

    response = client.put(
        f"/api/v1/teams/{team.id}",
        json={"name": "变更组", "leader_id": new_leader.id},
        headers=auth_headers,
    )

    assert response.status_code == 200
    db.refresh(team)
    assert team.created_by == new_leader.id
    assert db.query(TeamMember).filter_by(team_id=team.id, user_id=new_leader.id).first() is not None


def test_delete_team_with_tasks_is_rejected(client, auth_headers, normal_user, db):
    team = create_team(db, "开发组", normal_user.id)
    task = Task(
        title="已有任务",
        description="desc",
        status="pending",
        priority="medium",
        due_date=date(2026, 3, 23),
        created_by=normal_user.id,
        assigned_to=normal_user.id,
        team_id=team.id,
    )
    db.add(task)
    db.commit()

    response = client.delete(f"/api/v1/teams/{team.id}", headers=auth_headers)

    assert response.status_code == 400
    assert response.json()["detail"] == "团队下仍有关联任务，无法删除"
