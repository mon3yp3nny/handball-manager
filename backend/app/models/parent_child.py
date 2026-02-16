from sqlalchemy import Column, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base


class ParentChild(Base):
    __tablename__ = "parent_children"
    
    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    child_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    parent = relationship("User", back_populates="children", foreign_keys=[parent_id])
    child = relationship("Player", back_populates="parents", foreign_keys=[child_id])
