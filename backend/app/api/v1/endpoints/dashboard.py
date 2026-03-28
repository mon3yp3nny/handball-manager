"""Dashboard statistics endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from datetime import datetime, timedelta

from app.core.deps import get_db, get_current_user, require_admin
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
        Game.scheduled_at >= datetime.utcnow(),
        Game.scheduled_at <= datetime.utcnow() + timedelta(days=30),
        Game.status.in_(["scheduled", "in_progress"])
    ).count()
    
    # Upcoming events (next 30 days)
    upcoming_events = db.query(Event).filter(
        Event.start_time >= datetime.utcnow(),
        Event.start_time <= datetime.utcnow() + timedelta(days=30)
    ).count()
    
    # Users by role
    users_by_role = db.query(User.role, func.count(User.id)).group_by(User.role).all()
    
    # Recent activity (users created in last 7 days)
    recent_users = db.query(User).filter(
        User.created_at >= datetime.utcnow() - timedelta(days=7)
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
        User.created_at >= datetime.utcnow() - timedelta(days=7)
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
                Game.scheduled_at >= datetime.utcnow(),
                Game.scheduled_at <= datetime.utcnow() + timedelta(days=30)
            ).count(),
            "events_30d": db.query(Event).filter(
                Event.start_time >= datetime.utcnow(),
                Event.start_time <= datetime.utcnow() + timedelta(days=30)
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
        "timestamp": datetime.utcnow().isoformat()
    }
