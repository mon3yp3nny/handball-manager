from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.db.session import Base


class EventType(str, enum.Enum):
    TRAINING = "training"
    GAME = "game"
    MEETING = "meeting"
    TOURNAMENT = "tournament"
    OTHER = "other"


class EventVisibility(str, enum.Enum):
    TEAM = "team"
    CLUB_WIDE = "club_wide"
    AGE_GROUP = "age_group"


class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)  # Nullable for club-wide events
    event_type = Column(Enum(EventType), default=EventType.TRAINING)
    visibility = Column(Enum(EventVisibility), default=EventVisibility.TEAM)
    location = Column(String, nullable=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    team = relationship("Team", back_populates="events")
    attendance = relationship("Attendance", back_populates="event")
