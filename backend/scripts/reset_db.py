#!/usr/bin/env python3
"""DESTRUCTIVE: wipe all application data to a clean slate, then recreate the
admin account. Preserves the schema and `alembic_version` (migrations stay
intact). Intended to be run as a one-off Cloud Run Job before re-seeding.

TRUNCATE ... RESTART IDENTITY CASCADE clears every table (in any FK order)
and resets id sequences, so a fresh seed starts from id 1.
"""
import sys
sys.path.insert(0, "/app")  # so `app...` imports resolve when run as a job

from sqlalchemy import inspect, text

from app.db.session import SessionLocal, engine
from app.core import security
from app.models.user import User, UserRole


def main():
    inspector = inspect(engine)
    tables = [t for t in inspector.get_table_names() if t != "alembic_version"]
    if not tables:
        print("No tables found — nothing to reset.")
        return

    db = SessionLocal()
    try:
        db.execute(text(
            f'TRUNCATE TABLE {", ".join(tables)} RESTART IDENTITY CASCADE'
        ))
        db.commit()
        print(f"✓ Truncated {len(tables)} tables (kept alembic_version): "
              + ", ".join(sorted(tables)))

        admin = User(
            email="admin@handball.local",
            hashed_password=security.get_password_hash("Admin123!"),
            first_name="System",
            last_name="Administrator",
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
        )
        db.add(admin)
        db.commit()
        print("✓ Recreated admin: admin@handball.local / Admin123!")
        print("DONE — clean slate ready for seeding.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
