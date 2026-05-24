"""User model with OAuth support."""
import json
from sqlalchemy import Column, String, Text, Boolean, DateTime, Integer, ForeignKey, Table, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.utils.time import utcnow
import enum
from app.db.session import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    COACH = "coach"
    SUPERVISOR = "supervisor"
    PLAYER = "player"
    PARENT = "parent"


class ApprovalStatus(str, enum.Enum):
    """Registration approval state. New public sign-ups start PENDING and
    must be approved (coaches/supervisors by an admin; players/parents by
    the coach of their chosen team, admin as fallback). Everything created
    server-side (seed scripts, admin-created users) defaults APPROVED."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)  # Nullable for OAuth-only users
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    role = Column(Enum(UserRole), default=UserRole.PLAYER, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_oauth_only = Column(Boolean, default=False)  # True if user only has OAuth login
    # True once the user has completed initial role selection. Gates the OAuth
    # set-role endpoint to first-time use only — without this, any OAuth user
    # could re-call /oauth/set-role to escalate to admin (#88).
    role_selected = Column(Boolean, default=False, nullable=False, server_default="false")
    # JSON list of role values (e.g. '["coach","player","parent"]'). Holds the
    # full multi-role assignment; `role` above is the primary/legacy single role.
    roles_data = Column(Text, nullable=True)
    # Registration approval workflow. Defaults APPROVED at the DB level so all
    # existing/seeded users are unaffected; the public /auth/register endpoint
    # explicitly sets PENDING. requested_team_id is the team chosen at sign-up
    # (routes the approval to that team's coach and, for players, becomes the
    # Player.team_id once approved).
    approval_status = Column(
        Enum(ApprovalStatus), default=ApprovalStatus.APPROVED,
        server_default=ApprovalStatus.APPROVED.value, nullable=False, index=True,
    )
    # Soft reference to the team chosen at sign-up — intentionally NOT a FK.
    # A hard FK would create a users<->teams cycle (teams.coach_id already
    # points back here), which breaks metadata ordering. The team may also
    # be deleted later; every read of this column already handles a missing
    # team, so a dangling id is fine.
    requested_team_id = Column(Integer, nullable=True)
    approved_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    # Per-user secret token for the iCalendar (.ics) subscription URL. The
    # calendar endpoint is bearerless (calendar apps don't send Authorization
    # headers), so this token IS the credential. Generated lazily on first
    # access; rotate by deleting and re-creating.
    calendar_token = Column(String, unique=True, nullable=True, index=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    
    # Relationships
    player_profile = relationship("Player", back_populates="user", uselist=False)
    children = relationship("ParentChild", back_populates="parent", foreign_keys="ParentChild.parent_id")
    managed_teams = relationship("Team", back_populates="coach")
    oauth_accounts = relationship("OAuthAccount", back_populates="user", cascade="all, delete-orphan")
    sent_invitations = relationship("Invitation", foreign_keys="Invitation.invited_by", back_populates="inviter")
    activities = relationship("UserActivity", back_populates="user", order_by="desc(UserActivity.created_at)")
    
    @property
    def is_approved(self) -> bool:
        return self.approval_status == ApprovalStatus.APPROVED

    @property
    def roles(self) -> list:
        """Full list of UserRole enum values for this user.

        Reads roles_data JSON if populated; falls back to [self.role] for
        users created before multi-role support landed.
        """
        if self.roles_data:
            try:
                raw = json.loads(self.roles_data)
                parsed = [UserRole(v) for v in raw if v in UserRole._value2member_map_]
                if parsed:
                    return parsed
            except (ValueError, TypeError):
                pass
        return [self.role]

    @property
    def roles_list(self):
        """Backwards-compatible alias for `roles`."""
        return self.roles

    def has_role(self, check_role):
        """Check if user has the specified role (matches against any role in `roles`)."""
        if isinstance(check_role, UserRole):
            return check_role in self.roles
        return any(r.value == check_role for r in self.roles)

    def has_any_role(self, roles):
        """Check if user has any of the specified roles."""
        return any(self.has_role(r) for r in roles)

    def has_all_roles(self, roles):
        """Check if user has all specified roles."""
        return all(self.has_role(r) for r in roles)
