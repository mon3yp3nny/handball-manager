"""Add users.calendar_token for the iCalendar subscription feed.

Revision ID: 005
Revises: 004
Create Date: 2026-05-20

Backs the GET /api/v1/calendar/{token}.ics endpoint: every user gets a
per-user opaque token that calendar apps can subscribe to. The endpoint
is bearerless, so the token itself is the credential; rotate by
regenerating it.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = inspect(op.get_bind())
    cols = {c["name"] for c in inspector.get_columns("users")}
    if "calendar_token" not in cols:
        op.add_column("users", sa.Column("calendar_token", sa.String(), nullable=True))

    existing = {ix["name"] for ix in inspector.get_indexes("users")}
    if "ix_users_calendar_token" not in existing:
        op.create_index(
            "ix_users_calendar_token",
            "users",
            ["calendar_token"],
            unique=True,
        )


def downgrade() -> None:
    op.drop_index("ix_users_calendar_token", table_name="users")
    op.drop_column("users", "calendar_token")
