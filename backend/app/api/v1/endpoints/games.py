from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.utils.time import utcnow
from typing import List, Optional

from app.core.deps import get_db, get_current_user, require_coach, require_coach_or_supervisor
from app.core.permissions import can_access_team, team_ids_visible_to
from app.models.user import User, UserRole
from app.models.game import Game, GameStatus, GameType
from app.models.team import Team
from app.models.player import Player
from app.models.match_report import MatchReport
from app.schemas.game import GameCreate, GameUpdate, GameResponse, GameWithTeam, GameResultUpdate
from app.schemas.match_report import MatchReportCreate, MatchReportResponse, MatchReportUpdate
from app.schemas.common import PaginatedResponse
from app.websocket.manager import notify_resource

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[GameResponse])
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

    # Same RBAC as every other list endpoint (#91) — centralized.
    visible_team_ids = team_ids_visible_to(db, current_user)
    if visible_team_ids is not None:
        # None = admin/supervisor → no filter. Empty list = user has no
        # visible team → return no rows.
        query = query.filter(Game.team_id.in_(visible_team_ids)) if visible_team_ids else query.filter(False)

    if team_id:
        query = query.filter(Game.team_id == team_id)
    
    if status:
        query = query.filter(Game.status == status)
    
    if upcoming:
        now = utcnow()
        week_later = now + timedelta(days=7)
        query = query.filter(Game.scheduled_at >= now).filter(Game.scheduled_at <= week_later)
    
    total = query.count()
    games = query.order_by(Game.scheduled_at).offset(skip).limit(limit).all()
    
    return {
        "items": games,
        "total": total,
        "skip": skip,
        "limit": limit
    }


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
    if current_user.has_role(UserRole.COACH) and team.coach_id != current_user.id:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Not authorized to create games for this team")
    
    db_game = Game(**game_data.dict())
    db.add(db_game)
    db.commit()
    db.refresh(db_game)
    notify_resource("games", "created")
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
    # Single-team check → can_access_team — same predicate as the
    # team-detail and WS-subscribe endpoints. Replaces three hand-rolled
    # role branches with one call.
    if not can_access_team(current_user, game.team_id, db):
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
    if current_user.has_role(UserRole.COACH) and team.coach_id != current_user.id:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Not authorized to update this game")
    
    update_data = game_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(game, field, value)

    db.commit()
    db.refresh(game)
    notify_resource("games", "updated")
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
    if current_user.has_role(UserRole.COACH) and team.coach_id != current_user.id:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    game.home_score = result_data.home_score
    game.away_score = result_data.away_score
    game.status = result_data.status

    db.commit()
    db.refresh(game)
    notify_resource("games", "updated")
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
    if current_user.has_role(UserRole.COACH) and team.coach_id != current_user.id:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    db.delete(game)
    db.commit()
    notify_resource("games", "deleted")
    return {"message": "Game deleted"}


@router.get("/calendar/upcoming", response_model=List[GameResponse])
def get_calendar(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get upcoming games for calendar view"""
    now = utcnow()
    future = now + timedelta(days=days)
    
    query = db.query(Game).filter(
        Game.scheduled_at >= now,
        Game.scheduled_at <= future,
    )

    visible_team_ids = team_ids_visible_to(db, current_user)
    if visible_team_ids is not None:
        query = query.filter(Game.team_id.in_(visible_team_ids)) if visible_team_ids else query.filter(False)

    games = query.order_by(Game.scheduled_at).all()
    return games


def _user_can_edit_game(user: User, game: Game, db: Session) -> bool:
    """Coach of the game's team, or admin. Mirrors update_game/result rules."""
    if user.has_role(UserRole.ADMIN):
        return True
    if user.has_role(UserRole.COACH):
        team = db.query(Team).filter(Team.id == game.team_id).first()
        return bool(team and team.coach_id == user.id)
    if user.has_role(UserRole.SUPERVISOR):
        return True
    return False


@router.get("/{game_id}/report", response_model=MatchReportResponse)
def get_match_report(
    game_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Read the match report for a game (#131).

    Visibility follows the game itself — anyone who can see the game
    can read its report.
    """
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    if not can_access_team(current_user, game.team_id, db):
        raise HTTPException(status_code=403, detail="Not authorized")
    report = db.query(MatchReport).filter(MatchReport.game_id == game_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="No report for this game yet")
    return report


@router.post(
    "/{game_id}/report",
    response_model=MatchReportResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_match_report(
    game_id: int,
    payload: MatchReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_supervisor),
):
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    if not _user_can_edit_game(current_user, game, db):
        raise HTTPException(status_code=403, detail="Not authorized to write a report for this game")
    existing = db.query(MatchReport).filter(MatchReport.game_id == game_id).first()
    if existing:
        # PUT to update; POST is for the first write.
        raise HTTPException(status_code=409, detail="A report already exists for this game; use PUT")

    if payload.man_of_the_match_player_id is not None:
        mom = db.query(Player).filter(Player.id == payload.man_of_the_match_player_id).first()
        if not mom or mom.team_id != game.team_id:
            raise HTTPException(
                status_code=400,
                detail="MoM must be a player on the same team as the game",
            )

    report = MatchReport(
        game_id=game_id,
        author_id=current_user.id,
        body=payload.body,
        man_of_the_match_player_id=payload.man_of_the_match_player_id,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.put("/{game_id}/report", response_model=MatchReportResponse)
def update_match_report(
    game_id: int,
    payload: MatchReportUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_supervisor),
):
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    if not _user_can_edit_game(current_user, game, db):
        raise HTTPException(status_code=403, detail="Not authorized")
    report = db.query(MatchReport).filter(MatchReport.game_id == game_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="No report exists yet; use POST")

    data = payload.dict(exclude_unset=True)
    if "man_of_the_match_player_id" in data and data["man_of_the_match_player_id"] is not None:
        mom = db.query(Player).filter(Player.id == data["man_of_the_match_player_id"]).first()
        if not mom or mom.team_id != game.team_id:
            raise HTTPException(
                status_code=400,
                detail="MoM must be a player on the same team as the game",
            )
    for k, v in data.items():
        setattr(report, k, v)
    db.commit()
    db.refresh(report)
    return report


@router.delete("/{game_id}/report", status_code=status.HTTP_204_NO_CONTENT)
def delete_match_report(
    game_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_supervisor),
):
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    if not _user_can_edit_game(current_user, game, db):
        raise HTTPException(status_code=403, detail="Not authorized")
    report = db.query(MatchReport).filter(MatchReport.game_id == game_id).first()
    if not report:
        return {"message": "No report to delete"}
    db.delete(report)
    db.commit()
    return {"message": "Deleted"}
