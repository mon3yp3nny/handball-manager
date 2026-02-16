from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Text, Date, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.db.session import Base


class Position(str, enum.Enum):
    GOALKEEPER = "goalkeeper"
    LEFT_WING = "left_wing"
    LEFT_BACK = "left_back"
    CENTER_BACK = "center_back"
    RIGHT_BACK = "right_back"
    RIGHT_WING = "right_wing"
    PIVOT = "pivot"
    DEFENSE = "defense"


class Player(Base):
    __tablename__ = "players"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    jersey_number = Column(Integer, nullable=True)
    position = Column(Enum(Position), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    emergency_contact_name = Column(String, nullable=True)
    emergency_contact_phone = Column(String, nullable=True)
    
    # Statistics
    games_played = Column(Integer, default=0)
    goals_scored = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="player_profile")
    team = relationship("Team", back_populates="players")
    parents = relationship("ParentChild", back_populates="child", foreign_keys="ParentChild.child_id")
    attendance_records = relationship("Attendance", back_populates="player")
