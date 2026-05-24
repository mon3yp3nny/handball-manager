"""Fix approvalstatus enum label case to match SQLAlchemy's name-based storage.

Revision ID: 011
Revises: 010
Create Date: 2026-05-24

Migration 010 created the `approvalstatus` Postgres enum with lowercase
VALUES (pending/approved/rejected) and backfilled 'approved'. But the ORM
uses `Enum(ApprovalStatus)` with no values_callable, so SQLAlchemy reads
and writes by member NAME (PENDING/APPROVED/REJECTED) — matching every
other enum on the prod DB, which was bootstrapped via create_all. Reading
the lowercase 'approved' therefore blew up with:

    LookupError: 'approved' is not among the defined enum values.
    Possible values: PENDING, APPROVED, REJECTED

Rename the labels to the uppercase member names (RENAME VALUE updates every
row using them in place) and align the column default. Works whether the
DB came through 010's lowercase labels (prod) — both paths end uppercase.

SQLite (tests) builds the schema from the models via create_all, so this
Postgres-only migration is a no-op there.
"""
from typing import Sequence, Union

from alembic import op


revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_RENAMES = [("pending", "PENDING"), ("approved", "APPROVED"), ("rejected", "REJECTED")]


def upgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return
    # Guard each rename so it's idempotent (skip if already the new label).
    for old, new in _RENAMES:
        op.execute(
            f"""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM pg_enum e
                    JOIN pg_type t ON t.oid = e.enumtypid
                    WHERE t.typname = 'approvalstatus' AND e.enumlabel = '{old}'
                ) THEN
                    ALTER TYPE approvalstatus RENAME VALUE '{old}' TO '{new}';
                END IF;
            END $$;
            """
        )
    op.execute("ALTER TABLE users ALTER COLUMN approval_status SET DEFAULT 'APPROVED'")


def downgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return
    for old, new in _RENAMES:
        op.execute(
            f"""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM pg_enum e
                    JOIN pg_type t ON t.oid = e.enumtypid
                    WHERE t.typname = 'approvalstatus' AND e.enumlabel = '{new}'
                ) THEN
                    ALTER TYPE approvalstatus RENAME VALUE '{new}' TO '{old}';
                END IF;
            END $$;
            """
        )
    op.execute("ALTER TABLE users ALTER COLUMN approval_status SET DEFAULT 'approved'")
