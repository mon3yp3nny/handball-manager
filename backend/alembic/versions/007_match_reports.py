"""Add match_reports table (#131).

Revision ID: 007
Revises: 006
Create Date: 2026-05-20

One report per game — narrative write-up + optional MoM. Stored
separate from Game so the post-game flow can stay independent of the
score-entry flow.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "match_reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("game_id", sa.Integer(), sa.ForeignKey("games.id"), nullable=False),
        sa.Column("author_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "man_of_the_match_player_id",
            sa.Integer(),
            sa.ForeignKey("players.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("game_id", name="uq_match_reports_game"),
    )
    op.create_index("ix_match_reports_game_id", "match_reports", ["game_id"])
    op.create_index("ix_match_reports_author_id", "match_reports", ["author_id"])
    op.create_index(
        "ix_match_reports_mom",
        "match_reports",
        ["man_of_the_match_player_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_match_reports_mom", table_name="match_reports")
    op.drop_index("ix_match_reports_author_id", table_name="match_reports")
    op.drop_index("ix_match_reports_game_id", table_name="match_reports")
    op.drop_table("match_reports")
