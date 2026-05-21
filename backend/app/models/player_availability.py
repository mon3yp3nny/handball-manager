"""Player availability windows — RSVP's slower cousin (#136).

A row says "player X is unavailable from date A to date B because of
reason R". Used by coaches to plan around injuries / school exams /
holidays without re-asking each week. Distinct from Attendance (which
records what actually happened per event) and from RSVP (#126, per
event yes/no) — this is the broader stroke.
"""
from sqlalchemy import (
    Column, Integer, ForeignKey, Date, String, Text, Boolean, Enum, DateTime, Index
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.db.session import Base
from app.utils.time import utcnow


class AvailabilityReason(str, enum.Enum):
    INJURY = "injury"
    HOLIDAY = "holiday"
    EXAM = "exam"
    OTHER = "other"


class PlayerAvailability(Base):
    __tablename__ = "player_availability"
    # Hot lookup: "what is team X's availability this week" → index on
    # player_id + from_date for the date-range scan.
    __table_args__ = (
        Index("ix_player_availability_player_from", "player_id", "from_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(
        Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    from_date = Column(Date, nullable=False)
    # NULL = open-ended, e.g. "out until further notice".
    to_date = Column(Date, nullable=True)
    reason = Column(Enum(AvailabilityReason), nullable=False, default=AvailabilityReason.OTHER)
    note = Column(Text, nullable=True)
    # Medical entries are hidden from non-medical roles per #12; the flag
    # lives next to the row so the API filter is a single column check.
    is_medical = Column(Boolean, default=False, nullable=False)
    created_by = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True,
    )
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    player = relationship("Player", backref="availability_windows")
    creator = relationship("User", foreign_keys=[created_by])
