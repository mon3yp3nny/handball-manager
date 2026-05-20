"""FK indexes + unique constraints on attendance/players/parent_children.

Revision ID: 004
Revises: 003
Create Date: 2026-05-20

Addresses issues #89 (FK indexes) and #90 (unique constraints).

The legacy schema has no indexes on FK columns and no composite unique
constraints — every join scans, and duplicate attendance / shared jersey
numbers can sneak in. This migration:

1. De-duplicates existing data so the unique constraints can be applied
   (keeps the most recently recorded row per (player, game) and
    (player, event); nulls out duplicate jersey numbers).
2. Creates the missing FK indexes (idempotent via IF NOT EXISTS).
3. Creates the composite unique constraints.

Postgres and SQLite both treat NULL as distinct in UNIQUE, so a single
non-partial constraint suffices for the (player_id, game_id) /
(player_id, event_id) pairs even though one is always NULL.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ensure_user_activities_table() -> None:
    """Create user_activities if it's missing.

    The model exists in app/models/user_activity.py but no earlier
    migration creates the table — legacy prod got it via
    Base.metadata.create_all(); fresh dev DBs that come up purely via
    alembic don't have it at all. Either way, idempotent CREATE is safe.
    """
    inspector = inspect(op.get_bind())
    if "user_activities" in inspector.get_table_names():
        return

    op.create_table(
        "user_activities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("activity_type", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(), nullable=True),
        sa.Column("user_agent", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )


# (table, column, index_name) — kept here so up/down stay in sync.
_FK_INDEXES = [
    ("attendance", "player_id", "ix_attendance_player_id"),
    ("attendance", "game_id", "ix_attendance_game_id"),
    ("attendance", "event_id", "ix_attendance_event_id"),
    ("attendance", "recorded_by", "ix_attendance_recorded_by"),
    ("events", "team_id", "ix_events_team_id"),
    ("games", "team_id", "ix_games_team_id"),
    ("invitations", "team_id", "ix_invitations_team_id"),
    ("invitations", "invited_by", "ix_invitations_invited_by"),
    ("invitations", "accepted_by_user_id", "ix_invitations_accepted_by_user_id"),
    ("news", "team_id", "ix_news_team_id"),
    ("news", "author_id", "ix_news_author_id"),
    ("oauth_accounts", "user_id", "ix_oauth_accounts_user_id"),
    ("parent_children", "parent_id", "ix_parent_children_parent_id"),
    ("parent_children", "child_id", "ix_parent_children_child_id"),
    ("players", "team_id", "ix_players_team_id"),
    ("teams", "coach_id", "ix_teams_coach_id"),
    ("user_activities", "user_id", "ix_user_activities_user_id"),
    ("user_activities", "created_at", "ix_user_activities_created_at"),
]

_UNIQUE_CONSTRAINTS = [
    ("attendance", "uq_attendance_player_game", ("player_id", "game_id")),
    ("attendance", "uq_attendance_player_event", ("player_id", "event_id")),
    ("players", "uq_players_team_jersey", ("team_id", "jersey_number")),
    ("parent_children", "uq_parent_children_pair", ("parent_id", "child_id")),
]


def _dedup_data() -> None:
    """Remove duplicate rows so the unique constraints can be created.

    SQLite (tests) starts empty, so all of these are no-ops there. On the
    live Postgres these find at most a handful of stale rows.
    """
    bind = op.get_bind()

    # Attendance: keep the row with the largest id per (player, game) and
    # (player, event). id is monotonic and matches recorded_at ordering.
    bind.execute(sa.text("""
        DELETE FROM attendance
        WHERE game_id IS NOT NULL
          AND id NOT IN (
            SELECT MAX(id) FROM attendance
            WHERE game_id IS NOT NULL
            GROUP BY player_id, game_id
          )
    """))
    bind.execute(sa.text("""
        DELETE FROM attendance
        WHERE event_id IS NOT NULL
          AND id NOT IN (
            SELECT MAX(id) FROM attendance
            WHERE event_id IS NOT NULL
            GROUP BY player_id, event_id
          )
    """))

    # Players: null out jersey_number on duplicates within a team (keep
    # lowest id), then the UNIQUE applies cleanly.
    bind.execute(sa.text("""
        UPDATE players
        SET jersey_number = NULL
        WHERE jersey_number IS NOT NULL
          AND id NOT IN (
            SELECT MIN(id) FROM players
            WHERE jersey_number IS NOT NULL
            GROUP BY team_id, jersey_number
          )
    """))

    # Parent-child: collapse duplicate links to the lowest id.
    bind.execute(sa.text("""
        DELETE FROM parent_children
        WHERE id NOT IN (
            SELECT MIN(id) FROM parent_children
            GROUP BY parent_id, child_id
        )
    """))


def upgrade() -> None:
    _ensure_user_activities_table()
    _dedup_data()

    bind = op.get_bind()
    dialect = bind.dialect.name

    for table, column, name in _FK_INDEXES:
        # IF NOT EXISTS keeps re-runs and partially-applied prod states safe.
        if dialect == "postgresql":
            op.execute(f'CREATE INDEX IF NOT EXISTS {name} ON {table} ({column})')
        else:
            op.execute(f'CREATE INDEX IF NOT EXISTS {name} ON {table} ({column})')

    for table, name, cols in _UNIQUE_CONSTRAINTS:
        # SQLite can't add a named UNIQUE constraint via ALTER TABLE; use a
        # unique index there, which is semantically equivalent.
        if dialect == "sqlite":
            cols_csv = ", ".join(cols)
            op.execute(f'CREATE UNIQUE INDEX IF NOT EXISTS {name} ON {table} ({cols_csv})')
        else:
            op.create_unique_constraint(name, table, list(cols))


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    for table, name, _cols in _UNIQUE_CONSTRAINTS:
        if dialect == "sqlite":
            op.execute(f'DROP INDEX IF EXISTS {name}')
        else:
            op.drop_constraint(name, table, type_="unique")

    for _table, _column, name in _FK_INDEXES:
        op.execute(f'DROP INDEX IF EXISTS {name}')
