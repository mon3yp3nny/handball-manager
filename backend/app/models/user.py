"""User model with OAuth support."""
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Table, Enum, Text
from sqlalchemy.orm import relationship, validates
from datetime import datetime
import enum
from app.db.session import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    COACH = "coach"
    SUPERVISOR = "supervisor"
    PLAYER = "player"
    PARENT = "parent"


# Association table for user roles (many-to-many)
class UserRoles(Base):
    """Association table linking users to their roles."""
    __tablename__ = "user_roles"
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role = Column(String(20), primary_key=True)  # Store as string for flexibility


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)  # Nullable for OAuth-only users
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    # Keep primary_role for backward compatibility
    primary_role = Column(Enum(UserRole), default=UserRole.PLAYER, nullable=False)
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
    
    # Multi-role relationship
    _roles = relationship("UserRoles", backref="user", cascade="all, delete-orphan")
    
    @property
    def roles(self):
        """Get all roles as list of UserRole enums."""
        role_list = [UserRole(r.role) for r in self._roles]
        # Ensure primary_role is always included
        if self.primary_role not in role_list:
            role_list.append(self.primary_role)
        return role_list
    
    @roles.setter
    def roles(self, role_list):
        """Set roles from list of UserRole enums or strings."""
        self._roles = []
        for role in role_list:
            if isinstance(role, UserRole):
                role_value = role.value
            else:
                role_value = role
            self._roles.append(UserRoles(user_id=self.id, role=role_value))
        # Update primary_role to first role
        if role_list:
            self.primary_role = role_list[0] if isinstance(role_list[0], UserRole) else UserRole(role_list[0])
    
    @property
    def role(self):
        """Backward compatibility - returns primary role."""
        return self.primary_role
    
    def has_role(self, role):
        """Check if user has specific role."""
        if isinstance(role, UserRole):
            return role in self.roles
        return UserRole(role) in self.roles
    
    def has_any_role(self, roles):
        """Check if user has any of the specified roles."""
        return any(self.has_role(r) for r in roles)
    
    def has_all_roles(self, roles):
        """Check if user has all specified roles."""
        return all(self.has_role(r) for r in roles)
