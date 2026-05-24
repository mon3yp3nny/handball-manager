# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Handball Manager is a full-stack club management app for handball teams. It handles teams, players, games, events, attendance, news, and invitations with role-based access control (5 roles: Admin, Coach, Supervisor, Player, Parent). German-language UI labels for domain terms (positions, attendance statuses, event types).

**Repository:** https://github.com/mon3yp3nny/handball-manager

## Tech Stack

- **Backend:** FastAPI (Python 3.11), SQLAlchemy ORM, PostgreSQL 15, Alembic migrations
- **Frontend:** React 18, TypeScript 5.3, Vite, Tailwind CSS, Zustand (state), Axios (HTTP), TanStack Query (server state), react-hook-form (forms)
- **Auth:** JWT (access 30min / refresh 7 days) + OAuth (Google & Apple)
- **Real-time:** WebSocket with team-based subscriptions
- **Deployment:** Docker Compose, Google Cloud Run

## Commands

> **Development & testing run against the GCP deployment, not a local stack.**
> There is no local docker-compose / dev-server / mock-API workflow — features
> are deployed to Cloud Run and exercised on the live URLs. The only things run
> locally are the automated test/build gates below (they don't need a backend).

### Test & build gates (run locally / in CI before a deploy)
```bash
# Backend — full suite uses an in-memory SQLite fixture, no DB needed
cd backend
python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
pytest                                     # all tests
pytest tests/test_auth.py::test_login -v   # single test

# Frontend
cd frontend && npm install
npm run build      # type-check + production bundle
npm run lint       # ESLint
npx vitest run     # unit tests
```

### Deploy to GCP (the dev/test environment)
```bash
# Backend — scripts/start.sh runs `alembic upgrade head` on container start,
# so migrations apply automatically on deploy.
gcloud builds submit backend/ --tag gcr.io/handball-club-manager/handball-backend:latest --region europe-west1
gcloud run deploy handball-backend --image gcr.io/handball-club-manager/handball-backend:latest --region europe-west1

# Frontend — MUST use the same-origin build (nginx proxies /api + /ws so the
# auth cookie is first-party). Do NOT build the frontend any other way.
gcloud builds submit --config=cloudbuild-frontend.yaml --region=europe-west1 .

# Or the combined pipeline (backend+frontend tests, both images, both deploys):
gcloud builds submit --config=cloudbuild.yaml --region=europe-west1 .
```

### Database migrations
```bash
cd backend
alembic revision --autogenerate -m "description"   # author a migration
# Applied automatically on the next backend deploy (start.sh → alembic upgrade head).
```

## Architecture

### Backend (`backend/app/`)

Follows a **Model → Schema → Endpoint** pattern per entity:

```
models/       SQLAlchemy ORM models (11 tables)
schemas/      Pydantic request/response validation
api/v1/       FastAPI route handlers (12 endpoint modules)
  endpoints/  One file per resource (auth, oauth, teams, players, games, events, attendance, news, invitations, parents, users, health)
  api.py      Aggregates all routers under /api/v1
core/         Config (pydantic-settings), security (JWT), deps (DI), permissions (RBAC decorators), oauth, rate limiting
services/     Business logic (oauth_service.py, email_service.py)
db/           Database session + connection pooling
websocket/    ConnectionManager singleton for real-time team broadcasts
```

**Key entry point:** `app/main.py` — FastAPI app, CORS, WebSocket `/ws` endpoint, startup DB init.

### Frontend (`frontend/src/`)

```
pages/        14 page components (auth, dashboard, teams, players, games, events, attendance, news, calendar, profile, parent dashboard)
components/   Layout (AppLayout, Header, Sidebar, MobileNav)
store/        Zustand stores: authStore (auth state, UI state, notifications)
services/     api.ts (Axios client with httpOnly-cookie auth + CSRF + 401 refresh)
hooks/        useAuth, useWebSocket, useParent
types/        TypeScript interfaces for all domain entities
```

**Routing:** React Router v6 with `<ProtectedRoute>` wrapper. Public route: `/login` only.

**Path alias:** `@` maps to `src/` (configured in vite.config.ts and tsconfig.json).

### Data Model Relationships

- **User** has one optional **Player** profile, many **OAuthAccounts**, many **UserActivities**
- **Team** belongs to one Coach (**User**), has many **Players**, **Games**, **Events**, **News**, **Invitations**
- **ParentChild** links a Parent (**User**) to a Child (**Player**) — parents only see their own children's data
- **Attendance** links a **Player** to either a **Game** or **Event** (one nullable FK each)
- **Invitation** links an inviter (**User**) to a **Team** with a UUID verification token (7-day expiry)

### RBAC System

Permissions enforced at two levels:
1. **Endpoint level:** `require_roles()` decorator in `core/permissions.py` (e.g., `require_admin`, `require_coach_or_supervisor`)
2. **Query level:** Database queries filter results based on `current_user.role` — a Parent querying `/teams` only sees teams containing their children

### Authentication Flow

- **Traditional:** POST `/api/v1/auth/login` → JWT access + refresh tokens
- **OAuth:** Frontend sends provider token → backend verifies with provider → auto-creates/links user → returns JWT tokens + `needs_role_selection` flag → frontend calls `/api/v1/oauth/set-role`
- **Token refresh:** Axios interceptor auto-retries on 401 using refresh token

### WebSocket Protocol

Connect to `/ws`, send `{"token": "<JWT>"}` to authenticate, then `{"action": "subscribe_team", "team_id": N}` to receive real-time team updates.

## Test accounts (on the GCP deployment)

Seeded by `backend/scripts/setup_data.py` (idempotent; runnable on prod via the
`handball-seed` Cloud Run Job — see `backend/scripts/deploy-seed-job.sh`):
- `admin@handball.local` / `Admin123!` — Admin
- `max.mustermann@example.com` / `Test123!` — Coach (of two teams) + Player + Parent (good for the team-scoped sidebar switcher)
- `anna.schmidt@example.com` / `Test123!` — Supervisor + Parent
- `thomas.weber@example.com` / `Test123!` — Coach + Player
- `lisa.mueller@example.com` / `Test123!` — Player only
- `klaus.klein@example.com` / `Test123!` — Parent only

## API Documentation

On the deployed backend: Swagger at `/api/v1/docs`, ReDoc at `/api/v1/redoc`.

## Environment Variables

Configured on the Cloud Run services (not via local `.env`). Backend: `DATABASE_URL`,
`SECRET_KEY` (fails on the placeholder default), `GOOGLE_CLIENT_ID`, `APPLE_CLIENT_ID`,
`AUTH_COOKIE_SAMESITE`/`AUTH_COOKIE_SECURE`, `BACKEND_CORS_ORIGINS`, `FRONTEND_URL`.
Frontend (baked at build time): `VITE_API_URL` (`/api/v1`, same-origin),
`VITE_GOOGLE_CLIENT_ID`, `VITE_APPLE_CLIENT_ID`, `VITE_SENTRY_DSN`.
