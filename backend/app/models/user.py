"""User model with OAuth support."""
import json
from sqlalchemy import Column, String, Text, Boolean, DateTime, Integer, ForeignKey, Table, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.db.session import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    COACH = "coach"
    SUPERVISOR = "supervisor"
    PLAYER = "player"
    PARENT = "parent"


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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    player_profile = relationship("Player", back_populates="user", uselist=False)
    children = relationship("ParentChild", back_populates="parent", foreign_keys="ParentChild.parent_id")
    managed_teams = relationship("Team", back_populates="coach")
    oauth_accounts = relationship("OAuthAccount", back_populates="user", cascade="all, delete-orphan")
    sent_invitations = relationship("Invitation", foreign_keys="Invitation.invited_by", back_populates="inviter")
    activities = relationship("UserActivity", back_populates="user", order_by="desc(UserActivity.created_at)")
    
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
