"""Dashboard statistics endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from datetime import date, datetime, timedelta
from app.utils.time import utcnow
from typing import List, Optional

from app.core.deps import get_db, get_current_user, require_admin
from app.core.permissions import team_ids_visible_to
from app.models.user import User, UserRole
from app.models.team import Team
from app.models.player import Player
from app.models.game import Game
from app.models.event import Event

router = APIRouter()


@router.get("/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get dashboard statistics (available to all authenticated users)."""
    
    # Basic counts
    total_teams = db.query(Team).count()
    total_players = db.query(Player).count()
    total_users = db.query(User).count()
    
    # Upcoming games (next 30 days)
    upcoming_games = db.query(Game).filter(
        Game.scheduled_at >= utcnow(),
        Game.scheduled_at <= utcnow() + timedelta(days=30),
        Game.status.in_(["scheduled", "in_progress"])
    ).count()
    
    # Upcoming events (next 30 days)
    upcoming_events = db.query(Event).filter(
        Event.start_time >= utcnow(),
        Event.start_time <= utcnow() + timedelta(days=30)
    ).count()
    
    # Users by role
    users_by_role = db.query(User.role, func.count(User.id)).group_by(User.role).all()
    
    # Recent activity (users created in last 7 days)
    recent_users = db.query(User).filter(
        User.created_at >= utcnow() - timedelta(days=7)
    ).count()
    
    return {
        "total_teams": total_teams,
        "total_players": total_players,
        "total_users": total_users,
        "upcoming_games": upcoming_games,
        "upcoming_events": upcoming_events,
        "users_by_role": {str(role): count for role, count in users_by_role},
        "recent_activity": {
            "new_users_7d": recent_users
        }
    }


@router.get("/admin/summary")
def get_admin_dashboard_summary(
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Get detailed admin dashboard summary."""
    
    # Get all stats
    total_teams = db.query(Team).count()
    total_players = db.query(Player).count()
    total_games = db.query(Game).count()
    total_events = db.query(Event).count()
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    
    # Users by role
    users_by_role = db.query(User.role, func.count(User.id)).group_by(User.role).all()
    
    # Recent activity
    recent_users = db.query(User).filter(
        User.created_at >= utcnow() - timedelta(days=7)
    ).count()
    
    # Active games
    active_games = db.query(Game).filter(
        Game.status.in_(["scheduled", "in_progress"])
    ).count()
    
    # Teams without coaches
    teams_without_coach = db.query(Team).filter(Team.coach_id == None).count()
    
    # Players without teams
    players_without_team = db.query(Player).filter(Player.team_id == None).count()
    
    return {
        "counts": {
            "teams": total_teams,
            "players": total_players,
            "games": total_games,
            "events": total_events,
            "users": total_users,
            "active_users": active_users
        },
        "upcoming": {
            "games_30d": db.query(Game).filter(
                Game.scheduled_at >= utcnow(),
                Game.scheduled_at <= utcnow() + timedelta(days=30)
            ).count(),
            "events_30d": db.query(Event).filter(
                Event.start_time >= utcnow(),
                Event.start_time <= utcnow() + timedelta(days=30)
            ).count()
        },
        "users_by_role": {str(role): count for role, count in users_by_role},
        "recent_activity": {
            "new_users_7d": recent_users
        },
        "issues": {
            "teams_without_coach": teams_without_coach,
            "players_without_team": players_without_team,
            "active_games": active_games
        }
    }


@router.get("/widgets")
def get_dashboard_widgets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Forward-looking dashboard widgets — RBAC-scoped to what the user sees.

    Returns:
      - `next_match`: nearest upcoming Game in the user's visible teams,
        or null when there are none.
      - `upcoming_birthdays`: players whose date_of_birth's MONTH/DAY falls
        in the next 7 days (year-crossing handled). Visible only for
        players the user could already see on /players.

    Resolves #129.
    """
    now = utcnow()
    horizon = now + timedelta(days=7)

    visible_team_ids = team_ids_visible_to(db, current_user)

    # --- next match ---
    games_q = db.query(Game).filter(
        Game.scheduled_at >= now,
        Game.status.in_(["scheduled", "in_progress"]),
    )
    if visible_team_ids is not None:
        if not visible_team_ids:
            next_match_payload = None
            games_q = None  # short-circuit
        else:
            games_q = games_q.filter(Game.team_id.in_(visible_team_ids))

    next_match_payload = None
    if games_q is not None:
        nm = games_q.order_by(Game.scheduled_at.asc()).first()
        if nm:
            next_match_payload = {
                "id": nm.id,
                "team_id": nm.team_id,
                "opponent": nm.opponent,
                "location": nm.location,
                "scheduled_at": nm.scheduled_at.isoformat() if nm.scheduled_at else None,
                "is_home_game": nm.is_home_game,
            }

    # --- upcoming birthdays (next 7 days) ---
    players_q = db.query(Player).filter(Player.date_of_birth.isnot(None))
    if visible_team_ids is not None:
        if not visible_team_ids:
            players = []
        else:
            players = players_q.filter(Player.team_id.in_(visible_team_ids)).all()
    else:
        players = players_q.all()

    upcoming: list[dict] = []
    today = now.date()
    for p in players:
        dob: date = p.date_of_birth
        # Next-occurrence date this year; bump to next year if already past.
        try:
            nbd = dob.replace(year=today.year)
        except ValueError:
            # Feb 29 in a non-leap year — fall back to Feb 28.
            nbd = dob.replace(year=today.year, day=28)
        if nbd < today:
            try:
                nbd = dob.replace(year=today.year + 1)
            except ValueError:
                nbd = dob.replace(year=today.year + 1, day=28)
        days_until = (nbd - today).days
        if 0 <= days_until <= 7:
            upcoming.append(
                {
                    "player_id": p.id,
                    "team_id": p.team_id,
                    "first_name": (p.user.first_name if p.user else None),
                    "last_name": (p.user.last_name if p.user else None),
                    "date_of_birth": dob.isoformat(),
                    "days_until": days_until,
                    "turning": nbd.year - dob.year,
                }
            )
    upcoming.sort(key=lambda x: x["days_until"])

    return {
        "next_match": next_match_payload,
        "upcoming_birthdays": upcoming,
    }


@router.get("/health")
def get_system_health(
    db: Session = Depends(get_db)
):
    """Get system health status."""
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
        db_healthy = True
    except Exception as exc:
        db_status = str(exc)
        db_healthy = False
    
    return {
        "database": {
            "status": db_status,
            "healthy": db_healthy
        },
        "timestamp": utcnow().isoformat()
    }
