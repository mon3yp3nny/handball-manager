"""Match report — one narrative write-up per completed game (#131)."""
from sqlalchemy import Column, Integer, ForeignKey, Text, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.utils.time import utcnow


class MatchReport(Base):
    __tablename__ = "match_reports"
    # One report per game keeps the API simple (POST → 409 on retry).
    __table_args__ = (
        UniqueConstraint("game_id", name="uq_match_reports_game"),
    )

    id = Column(Integer, primary_key=True, index=True)
    # ON DELETE CASCADE: when a Game is deleted (e.g. by the team-delete
    # bulk path), the report goes with it. Without this, deleting a team
    # whose games have reports throws a 500 from the FK constraint and
    # the team gets stranded.
    game_id = Column(
        Integer,
        ForeignKey("games.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    # Plain markdown — the schema layer caps length; rendering is the
    # frontend's problem (we never inject this into HTML server-side).
    body = Column(Text, nullable=False)
    # Optional shout-out — nullable FK; deleting a player should null
    # this rather than cascade-delete the report.
    man_of_the_match_player_id = Column(
        Integer, ForeignKey("players.id", ondelete="SET NULL"), nullable=True, index=True,
    )
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    game = relationship("Game", backref="report")
    author = relationship("User", foreign_keys=[author_id])
    man_of_the_match = relationship("Player", foreign_keys=[man_of_the_match_player_id])
