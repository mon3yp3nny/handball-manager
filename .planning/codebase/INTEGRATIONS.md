# Integrations

## Database

**PostgreSQL 15** (via `psycopg2-binary`)
- ORM: SQLAlchemy 2.0 with async-compatible session management
- Migrations: Alembic with autogenerate support
- Connection: `DATABASE_URL` env var, pooled via `backend/app/db/session.py`
- 11 tables: User, Player, Team, Game, Event, Attendance, News, Invitation, ParentChild, OAuthAccount, UserActivity

## Authentication Providers

### Google OAuth
- Backend: `authlib` + `google-auth` for token verification
- Frontend: `@react-oauth/google` component
- Config: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
- Flow: Frontend gets Google token → POST `/api/v1/oauth/google` → backend verifies → creates/links user → returns JWT

### Apple Sign-In
- Backend: `PyJWT` for Apple JWT token verification
- Frontend: Apple JS SDK loaded dynamically on button click
- Config: `APPLE_CLIENT_ID`
- Flow: Frontend gets Apple identity token → POST `/api/v1/oauth/apple` → backend verifies → creates/links user → returns JWT

### JWT (Internal)
- Algorithm: HS256 (configurable via `ALGORITHM` env var)
- Access token: 30 min TTL (configurable)
- Refresh token: 7 day TTL
- Frontend: Axios interceptor auto-refreshes on 401

## WebSocket

- Native WebSocket at `/ws` endpoint in `backend/app/main.py`
- `ConnectionManager` singleton in `backend/app/websocket/manager.py`
- Protocol: authenticate with JWT token, subscribe to team channels
- Team-based broadcast for real-time updates

## Email

- **Mock implementation** in `backend/app/services/email_service.py`
- Logs emails to console, no actual sending
- Ready for SendGrid/AWS SES integration

## Cache / Task Queue

- **Redis:** Client configured (`redis==5.0.1`) but not actively used in endpoints
- **Celery:** Dependency installed (`celery==5.3.6`) but no task definitions found
- Both are infrastructure-ready but not wired up

## Rate Limiting

- `slowapi==0.1.9` configured in `backend/app/core/rate_limiting.py`
- Applied to auth endpoints to prevent brute force

## Logging

- `python-json-logger` for structured JSON log output
- Activity logging via `UserActivity` model for audit trail

## External Services (Production)

- **Google Cloud Run** — container hosting
- **Docker Compose** — orchestration (dev/staging)
- No external error tracking (Sentry, etc.) configured
- No external analytics configured
