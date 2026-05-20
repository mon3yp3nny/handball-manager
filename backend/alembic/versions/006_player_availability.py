"""Add player_availability table (#136).

Revision ID: 006
Revises: 005
Create Date: 2026-05-20

Stores "player is out from A to B because of <reason>" rows so coaches
can plan around injuries / school breaks / holidays without re-asking
each week. Distinct from Attendance (per-event, post-fact) and from
RSVP (#126, per-event yes/no/maybe) — coarser-grained.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "player_availability",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("player_id", sa.Integer(), sa.ForeignKey("players.id"), nullable=False),
        sa.Column("from_date", sa.Date(), nullable=False),
        sa.Column("to_date", sa.Date(), nullable=True),
        sa.Column("reason", sa.String(), nullable=False, server_default="other"),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "is_medical",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index(
        "ix_player_availability_player_id",
        "player_availability",
        ["player_id"],
    )
    op.create_index(
        "ix_player_availability_created_by",
        "player_availability",
        ["created_by"],
    )
    op.create_index(
        "ix_player_availability_player_from",
        "player_availability",
        ["player_id", "from_date"],
    )


def downgrade() -> None:
    op.drop_index("ix_player_availability_player_from", table_name="player_availability")
    op.drop_index("ix_player_availability_created_by", table_name="player_availability")
    op.drop_index("ix_player_availability_player_id", table_name="player_availability")
    op.drop_table("player_availability")
