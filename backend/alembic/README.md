# Alembic Migrations

Migrations are managed by Alembic. The `env.py` reads `DATABASE_URL` from the environment automatically.

## Common commands

```bash
cd backend

# Generate a new migration after model changes
alembic revision --autogenerate -m "describe your change"

# Apply all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show current revision
alembic current
```
