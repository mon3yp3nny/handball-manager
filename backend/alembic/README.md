# Alembic Migrations

Run migrations with:

```bash
cd backend
alembic init alembic
```

Then configure `alembic.ini`:
- Set `sqlalchemy.url` to your database URL
- Update `script_location = alembic`

Generate migrations:
```bash
alembic revision --autogenerate -m "Initial migration"
```

Apply migrations:
```bash
alembic upgrade head
```
