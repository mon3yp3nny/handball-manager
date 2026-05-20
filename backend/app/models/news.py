from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.utils.time import utcnow
from app.db.session import Base


class News(Base):
    __tablename__ = "news"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True, index=True)  # Null = global news
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    is_published = Column(Boolean, default=False)
    published_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    
    # Relationships
    team = relationship("Team", back_populates="news")
    author = relationship("User")
