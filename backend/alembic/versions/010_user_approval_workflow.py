"""Registration approval workflow fields on users.

Revision ID: 010
Revises: 009
Create Date: 2026-05-24

Adds the approval state used to gate new public sign-ups:

  approval_status    pending | approved | rejected  (server_default 'approved'
                     so every existing row stays approved; /auth/register sets
                     'pending' explicitly)
  requested_team_id  team chosen at sign-up — routes approval to that team's
                     coach and becomes Player.team_id on approval. Plain
                     integer (not a FK): a hard FK would create a
                     users<->teams cycle, and the value is read defensively.
  approved_by_id     approver (FK users, SET NULL on delete)
  approved_at        timestamp of the approve/reject decision
  rejection_reason   free text shown to a rejected user

SQLite (tests) rebuilds the schema from the models via create_all, so the
Postgres-only branch here is a no-op there.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    dialect = op.get_bind().dialect.name
    if dialect != "postgresql":
        return

    approval_status = sa.Enum(
        "pending", "approved", "rejected", name="approvalstatus"
    )
    approval_status.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "users",
        sa.Column(
            "approval_status", approval_status,
            server_default="approved", nullable=False,
        ),
    )
    op.create_index("ix_users_approval_status", "users", ["approval_status"])
    # requested_team_id is a plain integer (soft reference) — no FK, to
    # avoid a users<->teams cycle. approved_by_id is a normal self-FK.
    op.add_column("users", sa.Column("requested_team_id", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("approved_by_id", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("approved_at", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("rejection_reason", sa.Text(), nullable=True))
    op.create_foreign_key(
        "users_approved_by_id_fkey", "users", "users",
        ["approved_by_id"], ["id"], ondelete="SET NULL",
    )


def downgrade() -> None:
    dialect = op.get_bind().dialect.name
    if dialect != "postgresql":
        return

    op.drop_constraint("users_approved_by_id_fkey", "users", type_="foreignkey")
    op.drop_column("users", "rejection_reason")
    op.drop_column("users", "approved_at")
    op.drop_column("users", "approved_by_id")
    op.drop_column("users", "requested_team_id")
    op.drop_index("ix_users_approval_status", table_name="users")
    op.drop_column("users", "approval_status")
    sa.Enum(name="approvalstatus").drop(op.get_bind(), checkfirst=True)
