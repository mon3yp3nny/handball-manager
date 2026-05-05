#!/bin/sh
# Container entrypoint: handles first-time alembic adoption on legacy DBs,
# then runs migrations and starts the server.
#
# Legacy DB problem: Cloud SQL was originally bootstrapped via
# Base.metadata.create_all() before alembic was wired up. The schema exists
# but alembic_version does not, so `alembic upgrade head` tries to run
# migration 001 from scratch and fails with DuplicateObject.
#
# Fix: if `users` exists but `alembic_version` does not, stamp at 001 first.
# Once stamped, this branch never fires again.

set -e

ALEMBIC_PRESENT=$(psql "$DATABASE_URL" -tAc "SELECT 1 FROM information_schema.tables WHERE table_name='alembic_version'" 2>/dev/null || echo "")
USERS_PRESENT=$(psql "$DATABASE_URL" -tAc "SELECT 1 FROM information_schema.tables WHERE table_name='users'" 2>/dev/null || echo "")

if [ -z "$ALEMBIC_PRESENT" ] && [ "$USERS_PRESENT" = "1" ]; then
  echo "[start.sh] Legacy DB detected (users exists, alembic_version does not). Stamping at 001."
  alembic stamp 001
fi

alembic upgrade head
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8080}" --proxy-headers --forwarded-allow-ips='*'
