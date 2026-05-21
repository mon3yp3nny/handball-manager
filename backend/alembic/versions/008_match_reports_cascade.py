"""ON DELETE CASCADE on match_reports.game_id.

Revision ID: 008
Revises: 007
Create Date: 2026-05-21

Without CASCADE, team-delete (which bulk-deletes Game rows) stalls
with a foreign-key violation whenever any of the team's games has a
match report. The script's wipe step then silently fails on those
teams and they linger — the audit at the start of this commit caught
two such ghost teams.
"""
from typing import Optional, Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _existing_fk_name(table: str, column: str) -> Optional[str]:
    inspector = sa.inspect(op.get_bind())
    for fk in inspector.get_foreign_keys(table):
        if column in (fk.get("constrained_columns") or []):
            return fk.get("name")
    return None


def upgrade() -> None:
    dialect = op.get_bind().dialect.name
    if dialect == "postgresql":
        # Postgres: drop the auto-named FK (find it via the inspector
        # rather than guessing the name) and recreate with ON DELETE CASCADE.
        fk_name = _existing_fk_name("match_reports", "game_id")
        if fk_name:
            op.execute(
                f'ALTER TABLE match_reports DROP CONSTRAINT "{fk_name}"'
            )
        op.execute(
            "ALTER TABLE match_reports "
            "ADD CONSTRAINT match_reports_game_id_fkey "
            "FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE"
        )
    else:
        # SQLite has no per-FK constraint names to drop; recreating the
        # table inherits the new model definition's CASCADE so test runs
        # on SQLite stay correct without any work here. (Tests use
        # Base.metadata.create_all, not this migration, so the cascade
        # comes from the model definition directly.)
        pass


def downgrade() -> None:
    dialect = op.get_bind().dialect.name
    if dialect == "postgresql":
        fk_name = _existing_fk_name("match_reports", "game_id")
        if fk_name:
            op.execute(
                f'ALTER TABLE match_reports DROP CONSTRAINT "{fk_name}"'
            )
        op.execute(
            "ALTER TABLE match_reports "
            "ADD CONSTRAINT match_reports_game_id_fkey "
            "FOREIGN KEY (game_id) REFERENCES games(id)"
        )
