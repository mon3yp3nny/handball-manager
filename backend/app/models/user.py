"""User model with OAuth support."""
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Table, Enum
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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    player_profile = relationship("Player", back_populates="user", uselist=False)
    children = relationship("ParentChild", back_populates="parent", foreign_keys="ParentChild.parent_id")
    managed_teams = relationship("Team", back_populates="coach")
    oauth_accounts = relationship("OAuthAccount", back_populates="user", cascade="all, delete-orphan")
    sent_invitations = relationship("Invitation", foreign_keys="Invitation.invited_by", back_populates="inviter")
    activities = relationship("UserActivity", back_populates="user", order_by="desc(UserActivity.created_at)")
    
    # Multi-role support - roles are stored in JWT, primary role in DB
    @property
    def roles_list(self):
        """Get all roles as list - for backward compatibility returns single role."""
        return [self.role]
    
    def has_role(self, check_role):
        """Check if user has specific role - compares with primary role."""
        if isinstance(check_role, UserRole):
            return self.role == check_role
        return self.role.value == check_role
    
    def has_any_role(self, roles):
        """Check if user has any of the specified roles."""
        return any(self.has_role(r) for r in roles)
    
    def has_all_roles(self, roles):
        """Check if user has all specified roles."""
        return all(self.has_role(r) for r in roles)
