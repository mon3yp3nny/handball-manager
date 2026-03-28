"""User model with OAuth support."""
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Table, Enum, Text
from sqlalchemy.orm import relationship, validates
from datetime import datetime
import enum
import json
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
    role = Column(Enum(UserRole), default=UserRole.PLAYER, nullable=False)  # Primary role (backward compat)
    roles_data = Column(Text, nullable=True)  # JSON string of roles
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_oauth_only = Column(Boolean, default=False)  # True if user only has OAuth login
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    player_profile = relationship("Player", back_populates="user", uselist=False)
    children = relationship("ParentChild", back_populates="parent", foreign_keys="ParentChild.parent_id")
    managed_teams = relationship("Team", back_populates="coach")
    oauth_accounts = relationship("OAuthAccount", back_populates="user", cascade="all, delete-orphan")
    sent_invitations = relationship("Invitation", foreign_keys="Invitation.invited_by", back_populates="inviter")
    activities = relationship("UserActivity", back_populates="user", order_by="desc(UserActivity.created_at)")
    
    def _get_roles_list(self):
        """Get roles as list of strings."""
        if not self.roles_data:
            return [self.role.value] if self.role else [UserRole.PLAYER.value]
        try:
            roles = json.loads(self.roles_data)
            if isinstance(roles, list):
                return roles
            return [self.role.value] if self.role else [UserRole.PLAYER.value]
        except (json.JSONDecodeError, TypeError):
            return [self.role.value] if self.role else [UserRole.PLAYER.value]
    
    @property
    def roles(self):
        """Get/set roles as list of strings (for SQLAlchemy compatibility)."""
        return self._get_roles_list()
    
    @roles.setter
    def roles(self, value):
        """Set roles from list."""
        if isinstance(value, list):
            self.roles_data = json.dumps(value)
        else:
            self.roles_data = json.dumps([value]) if value else None
    
    @property
    def roles_list(self):
        """Get all roles as list of UserRole enums."""
        roles_data = self._get_roles_list()
        result = []
        for r in roles_data:
            try:
                result.append(UserRole(r))
            except (ValueError, TypeError):
                pass
        # Ensure primary role is always included
        if self.role:
            if self.role not in result:
                result.append(self.role)
        return result
    
    def has_role(self, role):
        """Check if user has specific role."""
        if isinstance(role, UserRole):
            return role.value in self._get_roles_list() or role == self.role
        return role in self._get_roles_list() or role == self.role.value
    
    def has_any_role(self, roles):
        """Check if user has any of the specified roles."""
        return any(self.has_role(r) for r in roles)
    
    def has_all_roles(self, roles):
        """Check if user has all specified roles."""
        return all(self.has_role(r) for r in roles)
    
    def set_roles(self, roles):
        """Set roles from list of UserRole enums or strings."""
        role_values = []
        for r in roles:
            if isinstance(r, UserRole):
                role_values.append(r.value)
            else:
                role_values.append(r)
        self.roles = role_values
        # Update primary role to first one
        if role_values:
            self.role = UserRole(role_values[0])
