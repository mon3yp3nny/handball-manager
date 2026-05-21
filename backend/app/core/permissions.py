"""Reusable role-based authorization dependencies."""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.user import User, UserRole


def team_ids_visible_to(db: Session, user: User) -> Optional[List[int]]:
    """The set of team ids this user is allowed to see (read-side RBAC).

    Returns:
        - ``None`` when the user can see every team (admin / supervisor) —
          callers treat this as "no team filter, skip the IN clause".
        - A sorted list otherwise; empty list = no visible teams.

    Mirrors the same rules ``can_access_team`` enforces for a single team
    but answers the inverse (list everything I can see) without an
    explicit team_id. Used by ``/dashboard/widgets``, ``/calendar``, and
    other list endpoints that need to filter by team membership; was
    duplicated as a private ``_team_ids_visible_to`` in two endpoints
    before (#91).
    """
    from app.models.team import Team
    from app.models.player import Player
    from app.models.parent_child import ParentChild

    if user.has_role(UserRole.ADMIN) or user.has_role(UserRole.SUPERVISOR):
        return None

    team_ids: set[int] = set()
    if user.has_role(UserRole.COACH):
        team_ids.update(
            tid for tid, in db.query(Team.id).filter(Team.coach_id == user.id).all()
        )
    if user.has_role(UserRole.PLAYER):
        player = db.query(Player).filter(Player.user_id == user.id).first()
        if player and player.team_id is not None:
            team_ids.add(player.team_id)
    if user.has_role(UserRole.PARENT):
        rows = (
            db.query(Player.team_id)
            .join(ParentChild, ParentChild.child_id == Player.id)
            .filter(ParentChild.parent_id == user.id)
            .distinct()
            .all()
        )
        team_ids.update(tid for tid, in rows if tid is not None)
    return sorted(team_ids)


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
            .scalar_subquery()
        )
        match = (
            db.query(Player.id)
            .filter(Player.id.in_(child_player_ids), Player.team_id == team_id)
            .first()
        )
        if match:
            return True

    return False


# `require_roles(...)` lived here but was dead code — no endpoint imported
# it — and its singular-role check was broken for multi-role users (max
# mustermann is coach+player+parent; only one of those would match
# `current_user.role`). The canonical dependency is `require_role([...])`
# in `core/deps.py` which uses `has_any_role()` and is multi-role aware.
# Removed per #91 — see commit history for the prior shape.
