"""Add roles_data column to users (multi-role JSON list).

Revision ID: 003
Revises: 002
Create Date: 2026-05-05

The column already exists on the legacy prod DB (added via raw ALTER TABLE
from the /setup/init endpoint). This migration is idempotent so it works on
both legacy DBs (where the column is already present) and clean DBs.

Issue context: roles_data was being written by the seed script but never
declared on the SQLAlchemy User model, so the API never read it back —
multi-role users like max.mustermann showed only a single role.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_cols = {c["name"] for c in inspector.get_columns("users")}
    if "roles_data" not in existing_cols:
        op.add_column("users", sa.Column("roles_data", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "roles_data")
