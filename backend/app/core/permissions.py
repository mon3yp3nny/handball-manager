"""Reusable role-based authorization dependencies."""
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.deps import get_current_user
from app.models.user import User, UserRole


def can_access_team(user: User, team_id: int, db: Session) -> bool:
    """Return True if ``user`` may access the team ``team_id``.

    Mirrors the role-based filtering applied by ``GET /teams/`` so that the
    team-detail endpoint and the WebSocket team subscription enforce the same
    visibility rules instead of being open to any authenticated caller.

    - Admin / Supervisor: every team
    - Coach: teams they manage
    - Player: their own team
    - Parent: teams of their children

    Roles are checked independently (not mutually exclusive) so multi-role
    users get the union of their access. Unlike the list endpoint, a Player
    with no team assignment is NOT granted blanket access to all teams here:
    the "discovery" allowance is acceptable for a filtered list but would be a
    data leak on a by-id detail lookup.
    """
    from app.models.team import Team
    from app.models.player import Player
    from app.models.parent_child import ParentChild

    if user.has_role(UserRole.ADMIN) or user.has_role(UserRole.SUPERVISOR):
        return True

    if user.has_role(UserRole.COACH):
        team = db.query(Team).filter(Team.id == team_id).first()
        if team and team.coach_id == user.id:
            return True

    if user.has_role(UserRole.PLAYER):
        player = db.query(Player).filter(Player.user_id == user.id).first()
        if player and player.team_id == team_id:
            return True

    if user.has_role(UserRole.PARENT):
        child_player_ids = (
            db.query(ParentChild.child_id)
            .filter(ParentChild.parent_id == user.id)
            .subquery()
        )
        match = (
            db.query(Player.id)
            .filter(Player.id.in_(child_player_ids), Player.team_id == team_id)
            .first()
        )
        if match:
            return True

    return False


def require_roles(*roles: UserRole):
    """FastAPI dependency that restricts access to the given roles.

    Usage::

        @router.get("/admin-only")
        def admin_view(user: User = Depends(require_roles(UserRole.ADMIN))):
            ...
    """
    allowed = set(roles)

    def _checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[r.value for r in allowed]}",
            )
        return current_user

    return _checker
