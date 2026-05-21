from sqlalchemy import Column, DateTime, Integer, ForeignKey, Enum, String, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.utils.time import utcnow
import enum
from app.db.session import Base


class AttendanceStatus(str, enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    EXCUSED = "excused"
    PENDING = "pending"


class Attendance(Base):
    __tablename__ = "attendance"
    # One attendance row per (player, game) or (player, event). NULL in the
    # other FK is treated as DISTINCT by both Postgres and SQLite, so a single
    # composite UNIQUE is enough — we don't need partial indexes.
    __table_args__ = (
        UniqueConstraint("player_id", "game_id", name="uq_attendance_player_game"),
        UniqueConstraint("player_id", "event_id", name="uq_attendance_player_event"),
    )

    id = Column(Integer, primary_key=True, index=True)
    # ON DELETE rules: when the parent Player / Game / Event goes (via
    # team-delete cascade or hard delete), the attendance row goes with
    # it. recorded_by is informational — keep the row, drop the link.
    player_id = Column(
        Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    game_id = Column(
        Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=True, index=True,
    )
    event_id = Column(
        Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=True, index=True,
    )
    status = Column(Enum(AttendanceStatus), default=AttendanceStatus.PENDING)
    notes = Column(String, nullable=True)
    recorded_by = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True,
    )
    recorded_at = Column(DateTime, default=utcnow)
    
    # Relationships
    player = relationship("Player", back_populates="attendance_records")
    game = relationship("Game", back_populates="attendance")
    event = relationship("Event", back_populates="attendance")
    recorder = relationship("User")
