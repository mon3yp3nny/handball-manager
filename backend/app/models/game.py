from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.db.session import Base


class GameStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class GameType(str, enum.Enum):
    LEAGUE = "league"
    TOURNAMENT = "tournament"
    FRIENDLY = "friendly"
    CUP = "cup"


class Game(Base):
    __tablename__ = "games"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    opponent = Column(String, nullable=False)
    location = Column(String, nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    game_type = Column(Enum(GameType), default=GameType.LEAGUE)
    status = Column(Enum(GameStatus), default=GameStatus.SCHEDULED)
    
    # Results (filled after game)
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    is_home_game = Column(Boolean, default=True)
    
    # Notes
    notes = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    team = relationship("Team", back_populates="games")
    attendance = relationship("Attendance", back_populates="game")
