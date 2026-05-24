from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.deps import get_db, get_current_user, require_admin, require_coach, require_coach_or_supervisor
from app.core.permissions import can_access_team, team_ids_visible_to
from app.models.user import User, UserRole
from app.models.team import Team
from app.models.player import Player
from app.models.game import Game, GameStatus
from app.models.event import Event
from app.models.news import News
from app.models.invitation import Invitation
from app.models.parent_child import ParentChild
from app.schemas.team import TeamCreate, TeamUpdate, TeamResponse, TeamWithPlayers
from app.schemas.common import PaginatedResponse
from app.schemas.registration import PublicTeam, MyTeams

router = APIRouter()


# Public — no auth. Feeds the team picker on the registration form so a
# prospective player/parent can choose the team whose coach approves them.
# Exposes id/name/age_group only. Declared before /{team_id} so "public"
# isn't captured as a team id.
@router.get("/public", response_model=List[PublicTeam])
def list_teams_public(db: Session = Depends(get_db)):
    return db.query(Team).order_by(Team.name).all()


# The current user's teams for the team-scoped sidebar. `managed` = teams
# they coach; `member` = their own player team + any team a child plays in.
# Declared before /{team_id} so "my" isn't parsed as a team id.
@router.get("/my", response_model=MyTeams)
def get_my_teams(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Admins/supervisors oversee the whole club, so every team is
    # "manageable" for them; coaches get the teams they actually coach.
    if current_user.has_any_role([UserRole.ADMIN, UserRole.SUPERVISOR]):
        managed = db.query(Team).order_by(Team.name).all()
    else:
        managed = (
            db.query(Team).filter(Team.coach_id == current_user.id).order_by(Team.name).all()
        )

    member_team_ids = set()
    own = db.query(Player).filter(Player.user_id == current_user.id).first()
    if own and own.team_id:
        member_team_ids.add(own.team_id)
    child_team_rows = (
        db.query(Player.team_id)
        .join(ParentChild, ParentChild.child_id == Player.id)
        .filter(ParentChild.parent_id == current_user.id, Player.team_id.isnot(None))
        .distinct()
        .all()
    )
    member_team_ids.update(tid for (tid,) in child_team_rows)

    member = (
        db.query(Team).filter(Team.id.in_(member_team_ids)).order_by(Team.name).all()
        if member_team_ids else []
    )
    return {"managed": managed, "member": member}


@router.get("/", response_model=PaginatedResponse[TeamResponse])
def get_teams(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    age_group: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Team)

    # Same RBAC as every other list endpoint. One quirk preserved from
    # the previous shape: a Player without a team assignment sees all
    # teams (so they can discover one to join) rather than an empty
    # list. team_ids_visible_to returns an empty list for that case;
    # detect it and skip the filter.
    visible_team_ids = team_ids_visible_to(db, current_user)
    if visible_team_ids is not None:
        if visible_team_ids:
            query = query.filter(Team.id.in_(visible_team_ids))
        elif current_user.has_role(UserRole.PLAYER):
            # Discovery for unassigned players — no filter.
            pass
        else:
            query = query.filter(False)

    if age_group:
        query = query.filter(Team.age_group == age_group)

    total = query.count()
    teams = query.offset(skip).limit(limit).all()

    return {
        "items": teams,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.post("/", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
def create_team(
    team_data: TeamCreate,
    db: Session = Depends(get_db),
    # Admin-only: coaches are assigned to teams by an admin and can only
    # manage their own (the update/delete endpoints below already enforce
    # team.coach_id == current_user.id for non-admin coaches). Without this
    # restriction a coach could bootstrap new teams freely (privilege
    # escalation caught by the E2E suite).
    current_user: User = Depends(require_admin)
):
    # Validate coach_id if provided
    if team_data.coach_id:
        coach = db.query(User).filter(User.id == team_data.coach_id, User.role == UserRole.COACH).first()
        if not coach:
            raise HTTPException(status_code=400, detail="Invalid coach_id: user not found or not a coach")

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
    from sqlalchemy.orm import joinedload
    team = db.query(Team).options(
        joinedload(Team.players).joinedload(Player.user)
    ).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if not can_access_team(current_user, team_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this team",
        )
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

    # Coaches can only update their own teams
    if current_user.role == UserRole.COACH and team.coach_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this team")

    # Validate coach_id if being updated
    update_data = team_data.dict(exclude_unset=True)
    if "coach_id" in update_data and update_data["coach_id"] is not None:
        coach = db.query(User).filter(User.id == update_data["coach_id"], User.role == UserRole.COACH).first()
        if not coach:
            raise HTTPException(status_code=400, detail="Invalid coach_id: user not found or not a coach")

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

    # Coaches can only delete their own teams
    if current_user.role == UserRole.COACH and team.coach_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this team")

    # Handle related records before deleting team
    db.query(Player).filter(Player.team_id == team_id).update({"team_id": None})
    db.query(Game).filter(Game.team_id == team_id).delete()
    db.query(Event).filter(Event.team_id == team_id).delete()
    db.query(News).filter(News.team_id == team_id).delete()
    db.query(Invitation).filter(Invitation.team_id == team_id).delete()

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
    
    if current_user.has_role(UserRole.COACH) and team.coach_id != current_user.id:
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
    
    if current_user.has_role(UserRole.COACH) and team.coach_id != current_user.id:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    player.team_id = None
    db.commit()
    db.refresh(team)
    return team


# Standard handball league scoring: 2 points per win, 1 per draw, 0 per loss.
_POINTS_WIN = 2
_POINTS_DRAW = 1


def _build_row(opponent: str, played: int, wins: int, draws: int, losses: int,
               gf: int, ga: int) -> dict:
    return {
        "opponent": opponent,
        "played": played,
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "goals_for": gf,
        "goals_against": ga,
        "goal_difference": gf - ga,
        "points": wins * _POINTS_WIN + draws * _POINTS_DRAW,
    }


@router.get("/{team_id}/standings")
def get_team_standings(
    team_id: int,
    date_from: Optional[datetime] = Query(None, alias="from"),
    date_to: Optional[datetime] = Query(None, alias="to"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Team standings computed from completed games (#128).

    Returns a season-wide `summary` row plus `per_opponent` rows sorted by
    points-then-goal-difference desc — a "Tabelle" view for the team.

    Optional `from` / `to` ISO date params narrow the window (no Season
    model yet; this is the simplest way to ask "this season only").

    Visibility: the same RBAC as GET /teams/{id} — admin/supervisor and
    coaches of the team see it; players see their team; parents see
    their children's team.
    """
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if not can_access_team(current_user, team_id, db):
        raise HTTPException(status_code=403, detail="Access denied to this team")

    q = db.query(Game).filter(
        Game.team_id == team_id,
        Game.status == GameStatus.COMPLETED,
        Game.home_score.isnot(None),
        Game.away_score.isnot(None),
    )
    if date_from is not None:
        q = q.filter(Game.scheduled_at >= date_from)
    if date_to is not None:
        q = q.filter(Game.scheduled_at <= date_to)

    games = q.order_by(Game.scheduled_at.asc()).all()

    # Aggregate per opponent and overall in one pass.
    agg: dict[str, dict] = {}
    summary = {"played": 0, "wins": 0, "draws": 0, "losses": 0,
               "goals_for": 0, "goals_against": 0}

    for g in games:
        # The team's score regardless of home/away orientation.
        if g.is_home_game:
            gf, ga = g.home_score, g.away_score
        else:
            gf, ga = g.away_score, g.home_score

        row = agg.setdefault(
            g.opponent,
            {"opponent": g.opponent, "played": 0, "wins": 0, "draws": 0,
             "losses": 0, "goals_for": 0, "goals_against": 0},
        )
        row["played"] += 1
        row["goals_for"] += gf
        row["goals_against"] += ga
        if gf > ga:
            row["wins"] += 1
            summary["wins"] += 1
        elif gf == ga:
            row["draws"] += 1
            summary["draws"] += 1
        else:
            row["losses"] += 1
            summary["losses"] += 1
        summary["played"] += 1
        summary["goals_for"] += gf
        summary["goals_against"] += ga

    summary_row = _build_row(
        team.name, summary["played"], summary["wins"], summary["draws"],
        summary["losses"], summary["goals_for"], summary["goals_against"],
    )

    per_opponent = [
        _build_row(r["opponent"], r["played"], r["wins"], r["draws"],
                   r["losses"], r["goals_for"], r["goals_against"])
        for r in agg.values()
    ]
    per_opponent.sort(key=lambda r: (-r["points"], -r["goal_difference"], r["opponent"]))

    return {
        "team_id": team.id,
        "team_name": team.name,
        "from": date_from.isoformat() if date_from else None,
        "to": date_to.isoformat() if date_to else None,
        "summary": summary_row,
        "per_opponent": per_opponent,
    }
