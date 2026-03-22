from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from models import Team, TeamMember, User, Task

router = APIRouter(prefix="/teams", tags=["teams"])


def ok(data):
    return {"code": 0, "message": "ok", "data": data}


class TeamPayload(BaseModel):
    name: str
    leader_id: int | None = None


class TeamMemberPayload(BaseModel):
    user_id: int


def serialize_member(member: TeamMember):
    return {
        "user_id": member.user_id,
        "username": member.user.username if member.user else None,
        "email": member.user.email if member.user else None,
        "joined_at": member.joined_at.isoformat() if member.joined_at else None,
    }


def serialize_team(team: Team):
    return {
        "id": team.id,
        "name": team.name,
        "leader_id": team.created_by,
        "created_by": team.created_by,
        "created_at": team.created_at.isoformat() if team.created_at else None,
    }


def get_team_or_404(db: Session, team_id: int) -> Team:
    team = db.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="团队不存在")
    return team


def is_team_member(db: Session, team_id: int, user_id: int) -> bool:
    return db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == user_id,
    ).first() is not None


def ensure_team_access(team: Team, current_user: User, db: Session) -> Team:
    if current_user.is_admin or team.created_by == current_user.id or is_team_member(db, team.id, current_user.id):
        return team
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问该团队")


def ensure_team_manage(team: Team, current_user: User) -> Team:
    if current_user.is_admin or team.created_by == current_user.id:
        return team
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权修改该团队")


@router.get("")
def list_teams(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.is_admin:
        teams = db.query(Team).order_by(Team.id.asc()).all()
    else:
        teams = db.query(Team).filter(
            (Team.created_by == current_user.id)
            | Team.members.any(TeamMember.user_id == current_user.id)
        ).order_by(Team.id.asc()).all()
    return ok([serialize_team(team) for team in teams])


@router.post("")
def create_team(
    payload: TeamPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    leader_id = payload.leader_id or current_user.id
    if not current_user.is_admin and leader_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权为其他用户创建团队")

    leader = db.get(User, leader_id)
    if not leader or not leader.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="负责人不存在")

    team = Team(name=payload.name, created_by=leader_id)
    db.add(team)
    db.flush()
    db.add(TeamMember(team_id=team.id, user_id=leader_id))
    db.commit()
    db.refresh(team)
    return ok(serialize_team(team))


@router.get("/{team_id}")
def get_team(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    team = ensure_team_access(get_team_or_404(db, team_id), current_user, db)
    members = db.query(TeamMember).filter(TeamMember.team_id == team.id).order_by(TeamMember.user_id.asc()).all()
    data = serialize_team(team)
    data["members"] = [serialize_member(member) for member in members]
    return ok(data)


@router.put("/{team_id}")
def update_team(
    team_id: int,
    payload: TeamPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    team = ensure_team_manage(get_team_or_404(db, team_id), current_user)
    leader_id = payload.leader_id if payload.leader_id is not None else team.created_by
    leader = db.get(User, leader_id)
    if not leader or not leader.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="负责人不存在")

    team.name = payload.name
    team.created_by = leader_id
    if not is_team_member(db, team.id, leader_id):
        db.add(TeamMember(team_id=team.id, user_id=leader_id))

    db.commit()
    db.refresh(team)
    return ok(serialize_team(team))


@router.delete("/{team_id}")
def delete_team(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    team = ensure_team_manage(get_team_or_404(db, team_id), current_user)
    has_tasks = db.query(Task).filter(Task.team_id == team.id).first() is not None
    if has_tasks:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="团队下仍有关联任务，无法删除")
    db.query(TeamMember).filter(TeamMember.team_id == team.id).delete()
    db.delete(team)
    db.commit()
    return ok(None)


@router.get("/{team_id}/members")
def list_team_members(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    team = ensure_team_access(get_team_or_404(db, team_id), current_user, db)
    members = db.query(TeamMember).filter(TeamMember.team_id == team.id).order_by(TeamMember.user_id.asc()).all()
    return ok([serialize_member(member) for member in members])


@router.post("/{team_id}/members")
def add_team_member(
    team_id: int,
    payload: TeamMemberPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    team = ensure_team_manage(get_team_or_404(db, team_id), current_user)
    user = db.get(User, payload.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    if is_team_member(db, team.id, payload.user_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户已在团队中")

    member = TeamMember(team_id=team.id, user_id=payload.user_id)
    db.add(member)
    db.commit()
    db.refresh(member)
    return ok(serialize_member(member))


@router.delete("/{team_id}/members/{user_id}")
def remove_team_member(
    team_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    team = ensure_team_manage(get_team_or_404(db, team_id), current_user)
    member = db.query(TeamMember).filter(
        TeamMember.team_id == team.id,
        TeamMember.user_id == user_id,
    ).first()
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="成员不存在")
    if team.created_by == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能移除团队负责人")

    db.delete(member)
    db.commit()
    return ok(None)
