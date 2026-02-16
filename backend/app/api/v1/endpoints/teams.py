from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.deps import get_db, get_current_user, require_coach, require_coach_or_supervisor
from app.models.user import User, UserRole
from app.models.team import Team
from app.models.player import Player
from app.schemas.team import TeamCreate, TeamUpdate, TeamResponse, TeamWithPlayers

router = APIRouter()


@router.get("/", response_model=List[TeamResponse])
def get_teams(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    age_group: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Team)
    
    # Filter by role
    if current_user.role == UserRole.PLAYER:
        # Players see only their team
        player = db.query(Player).filter(Player.user_id == current_user.id).first()
        if player and player.team_id:
            query = query.filter(Team.id == player.team_id)
    elif current_user.role == UserRole.PARENT:
        # Parents see teams of their children
        from app.models.parent_child import ParentChild
        child_player_ids = db.query(ParentChild.child_id).filter(ParentChild.parent_id == current_user.id).subquery()
        child_team_ids = db.query(Player.team_id).filter(Player.id.in_(child_player_ids)).subquery()
        query = query.filter(Team.id.in_(child_team_ids))
    elif current_user.role == UserRole.COACH:
        # Coaches see teams they manage
        query = query.filter(Team.coach_id == current_user.id)
    
    if age_group:
        query = query.filter(Team.age_group == age_group)
    
    teams = query.offset(skip).limit(limit).all()
    return teams


@router.post("/", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
def create_team(
    team_data: TeamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach)
):
    db_team = Team(**team_data.dict())
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    return db_team


@router.get("/{team_id}", response_model=TeamWithPlayers)
def get_team(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


@router.put("/{team_id}", response_model=TeamResponse)
def update_team(
    team_id: int,
    team_data: TeamUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach)
):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Coaches can only update their own teams (unless admin)
    if current_user.role == UserRole.COACH and team.coach_id != current_user.id:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Not authorized to update this team")
    
    update_data = team_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(team, field, value)
    
    db.commit()
    db.refresh(team)
    return team


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach)
):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    if current_user.role == UserRole.COACH and team.coach_id != current_user.id:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Not authorized to delete this team")
    
    db.delete(team)
    db.commit()
    return {"message": "Team deleted"}


@router.post("/{team_id}/players/{player_id}", response_model=TeamWithPlayers)
def add_player_to_team(
    team_id: int,
    player_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach)
):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    if current_user.role == UserRole.COACH and team.coach_id != current_user.id:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    player.team_id = team_id
    db.commit()
    db.refresh(team)
    return team


@router.delete("/{team_id}/players/{player_id}", response_model=TeamWithPlayers)
def remove_player_from_team(
    team_id: int,
    player_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach)
):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    if current_user.role == UserRole.COACH and team.coach_id != current_user.id:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    player.team_id = None
    db.commit()
    db.refresh(team)
    return team
