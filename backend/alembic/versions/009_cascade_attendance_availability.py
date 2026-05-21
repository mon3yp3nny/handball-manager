"""Comprehensive ON DELETE rules across attendance + player_availability.

Revision ID: 009
Revises: 008
Create Date: 2026-05-21

Follow-up to 008: that one was scoped to match_reports → games, but
team-delete still failed because attendance rows referencing the
team's games + events also had no CASCADE. Sweeping the rest:

  attendance.player_id          → CASCADE  (player gone → rows gone)
  attendance.game_id            → CASCADE  (game gone → rows gone)
  attendance.event_id           → CASCADE  (event gone → rows gone)
  attendance.recorded_by        → SET NULL (keep row, drop link)
  player_availability.player_id → CASCADE
  player_availability.created_by → SET NULL

SQLite has no per-FK constraint names to drop, but tests boot via
Base.metadata.create_all using the updated model definitions — so the
SQLite branch here is intentionally a no-op.
"""
from typing import Optional, Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (table, column, parent_table, parent_column, new_action, new_name)
_FK_CHANGES = [
    ("attendance", "player_id", "players", "id", "CASCADE",
     "attendance_player_id_fkey"),
    ("attendance", "game_id", "games", "id", "CASCADE",
     "attendance_game_id_fkey"),
    ("attendance", "event_id", "events", "id", "CASCADE",
     "attendance_event_id_fkey"),
    ("attendance", "recorded_by", "users", "id", "SET NULL",
     "attendance_recorded_by_fkey"),
    ("player_availability", "player_id", "players", "id", "CASCADE",
     "player_availability_player_id_fkey"),
    ("player_availability", "created_by", "users", "id", "SET NULL",
     "player_availability_created_by_fkey"),
]


def _existing_fk_name(table: str, column: str) -> Optional[str]:
    inspector = sa.inspect(op.get_bind())
    for fk in inspector.get_foreign_keys(table):
        if column in (fk.get("constrained_columns") or []):
            return fk.get("name")
    return None


def upgrade() -> None:
    dialect = op.get_bind().dialect.name
    if dialect != "postgresql":
        # SQLite: tests rebuild the schema from models via create_all, so
        # the updated ondelete clauses on the model take effect there.
        return

    for table, col, parent, parent_col, action, new_name in _FK_CHANGES:
        existing = _existing_fk_name(table, col)
        if existing:
            op.execute(f'ALTER TABLE {table} DROP CONSTRAINT "{existing}"')
        op.execute(
            f'ALTER TABLE {table} '
            f'ADD CONSTRAINT {new_name} '
            f'FOREIGN KEY ({col}) REFERENCES {parent}({parent_col}) '
            f'ON DELETE {action}'
        )


def downgrade() -> None:
    dialect = op.get_bind().dialect.name
    if dialect != "postgresql":
        return

    for table, col, parent, parent_col, _action, name in _FK_CHANGES:
        existing = _existing_fk_name(table, col)
        if existing:
            op.execute(f'ALTER TABLE {table} DROP CONSTRAINT "{existing}"')
        op.execute(
            f'ALTER TABLE {table} '
            f'ADD CONSTRAINT {name} '
            f'FOREIGN KEY ({col}) REFERENCES {parent}({parent_col})'
        )
