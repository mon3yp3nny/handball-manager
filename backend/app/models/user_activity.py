from sqlalchemy import Column, DateTime, Integer, ForeignKey, String, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.db.session import Base


class ActivityType(str, enum.Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    PROFILE_UPDATE = "profile_update"
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    ROLE_CHANGE = "role_change"


class UserActivity(Base):
    __tablename__ = "user_activities"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    activity_type = Column(Enum(ActivityType), nullable=False)
    description = Column(Text, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="activities")
