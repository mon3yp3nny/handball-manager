from sqlalchemy import Column, DateTime, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base


class ParentChild(Base):
    __tablename__ = "parent_children"
    # A parent shouldn't be linked to the same child twice. The composite is
    # also the hot lookup key (parent_id WHERE child_id, child_id WHERE parent_id).
    __table_args__ = (
        UniqueConstraint("parent_id", "child_id", name="uq_parent_children_pair"),
    )

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    child_id = Column(Integer, ForeignKey("players.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    parent = relationship("User", back_populates="children", foreign_keys=[parent_id])
    child = relationship("Player", back_populates="parents", foreign_keys=[child_id])
