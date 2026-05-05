"""Add role_selected flag to users

Revision ID: 002
Revises: 001
Create Date: 2026-05-05

Closes #88: gates the OAuth /set-role endpoint to first-time use only.
Existing rows are backfilled to true — they have already chosen a role and
must not be allowed to re-elect via the self-service endpoint.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "role_selected",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    # Backfill: every existing user has already had their role established by
    # admin/seed/registration. Lock them out of /oauth/set-role.
    op.execute("UPDATE users SET role_selected = true")


def downgrade() -> None:
    op.drop_column("users", "role_selected")
