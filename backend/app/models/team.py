from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base


class Team(Base):
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    age_group = Column(String, nullable=True)  # e.g., "U12", "U14", "Adult"
    coach_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    coach = relationship("User", back_populates="managed_teams")
    players = relationship("Player", back_populates="team")
    games = relationship("Game", back_populates="team")
    events = relationship("Event", back_populates="team")
    news = relationship("News", back_populates="team")
    invitations = relationship("Invitation", back_populates="team")
