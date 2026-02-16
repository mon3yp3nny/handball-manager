from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional

from app.core.deps import get_db, get_current_user, require_coach, require_coach_or_supervisor
from app.models.user import User, UserRole
from app.models.game import Game, GameStatus, GameType
from app.models.team import Team
from app.models.player import Player
from app.schemas.game import GameCreate, GameUpdate, GameResponse, GameWithTeam, GameResultUpdate

router = APIRouter()


@router.get("/", response_model=List[GameResponse])
def get_games(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    team_id: Optional[int] = None,
    status: Optional[GameStatus] = None,
    upcoming: bool = Query(False, description="Get only upcoming games (next 7 days)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Game).join(Team, Game.team_id == Team.id)
    
    # Role-based filtering
    if current_user.role == UserRole.PLAYER:
        current_player = db.query(Player).filter(Player.user_id == current_user.id).first()
        if current_player and current_player.team_id:
            query = query.filter(Game.team_id == current_player.team_id)
    elif current_user.role == UserRole.PARENT:
        from app.models.parent_child import ParentChild
        child_team_ids = db.query(Player.team_id).join(
            ParentChild, ParentChild.child_id == Player.id
        ).filter(ParentChild.parent_id == current_user.id).distinct().subquery()
        query = query.filter(Game.team_id.in_(child_team_ids))
    elif current_user.role == UserRole.COACH:
        coach_team_ids = db.query(Team.id).filter(Team.coach_id == current_user.id).subquery()
        query = query.filter(Game.team_id.in_(coach_team_ids))
    
    if team_id:
        query = query.filter(Game.team_id == team_id)
    
    if status:
        query = query.filter(Game.status == status)
    
    if upcoming:
        now = datetime.utcnow()
        week_later = now + timedelta(days=7)
        query = query.filter(Game.scheduled_at >= now).filter(Game.scheduled_at <= week_later)
    
    games = query.order_by(Game.scheduled_at).offset(skip).limit(limit).all()
    return games


@router.post("/", response_model=GameResponse, status_code=status.HTTP_201_CREATED)
def create_game(
    game_data: GameCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach)
):
    # Verify team exists
    team = db.query(Team).filter(Team.id == game_data.team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Coaches can only create games for their teams
    if current_user.role == UserRole.COACH and team.coach_id != current_user.id:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Not authorized to create games for this team")
    
    db_game = Game(**game_data.dict())
    db.add(db_game)
    db.commit()
    db.refresh(db_game)
    return db_game


@router.get("/{game_id}", response_model=GameWithTeam)
def get_game(
    game_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Authorization check
    if current_user.role == UserRole.PLAYER:
        current_player = db.query(Player).filter(Player.user_id == current_user.id).first()
        if current_player and game.team_id != current_player.team_id:
            raise HTTPException(status_code=403, detail="Not authorized")
    elif current_user.role == UserRole.PARENT:
        from app.models.parent_child import ParentChild
        child_team_ids = db.query(Player.team_id).join(
            ParentChild, ParentChild.child_id == Player.id
        ).filter(ParentChild.parent_id == current_user.id).distinct().subquery()
        if game.team_id not in [tid for tid, in db.query(child_team_ids).all()]:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    return game


@router.put("/{game_id}", response_model=GameResponse)
def update_game(
    game_id: int,
    game_data: GameUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach)
):
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Authorization
    team = db.query(Team).filter(Team.id == game.team_id).first()
    if current_user.role == UserRole.COACH and team.coach_id != current_user.id:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Not authorized to update this game")
    
    update_data = game_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(game, field, value)
    
    db.commit()
    db.refresh(game)
    return game


@router.patch("/{game_id}/result", response_model=GameResponse)
def update_game_result(
    game_id: int,
    result_data: GameResultUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_supervisor)
):
    """Update game result after the game"""
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Authorization
    team = db.query(Team).filter(Team.id == game.team_id).first()
    if current_user.role == UserRole.COACH and team.coach_id != current_user.id:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    game.home_score = result_data.home_score
    game.away_score = result_data.away_score
    game.status = result_data.status
    
    db.commit()
    db.refresh(game)
    return game


@router.delete("/{game_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_game(
    game_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach)
):
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    team = db.query(Team).filter(Team.id == game.team_id).first()
    if current_user.role == UserRole.COACH and team.coach_id != current_user.id:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    db.delete(game)
    db.commit()
    return {"message": "Game deleted"}


@router.get("/calendar/upcoming", response_model=List[GameResponse])
def get_calendar(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get upcoming games for calendar view"""
    now = datetime.utcnow()
    future = now + timedelta(days=days)
    
    query = db.query(Game).filter(
        Game.scheduled_at >= now,
        Game.scheduled_at <= future
    )
    
    # Filter by role
    if current_user.role == UserRole.PLAYER:
        current_player = db.query(Player).filter(Player.user_id == current_user.id).first()
        if current_player and current_player.team_id:
            query = query.filter(Game.team_id == current_player.team_id)
    elif current_user.role == UserRole.PARENT:
        from app.models.parent_child import ParentChild
        child_team_ids = db.query(Player.team_id).join(
            ParentChild, ParentChild.child_id == Player.id
        ).filter(ParentChild.parent_id == current_user.id).distinct().subquery()
        query = query.filter(Game.team_id.in_(child_team_ids))
    elif current_user.role == UserRole.COACH:
        coach_team_ids = db.query(Team.id).filter(Team.coach_id == current_user.id).subquery()
        query = query.filter(Game.team_id.in_(coach_team_ids))
    
    games = query.order_by(Game.scheduled_at).all()
    return games
