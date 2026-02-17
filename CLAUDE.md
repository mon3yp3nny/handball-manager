# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Handball Manager is a full-stack club management app for handball teams. It handles teams, players, games, events, attendance, news, and invitations with role-based access control (5 roles: Admin, Coach, Supervisor, Player, Parent). German-language UI labels for domain terms (positions, attendance statuses, event types).

**Repository:** https://github.com/mon3yp3nny/handball-manager

## Tech Stack

- **Backend:** FastAPI (Python 3.11), SQLAlchemy ORM, PostgreSQL 15, Alembic migrations
- **Frontend:** React 18, TypeScript 5.3, Vite, Tailwind CSS, Zustand (state), Axios (HTTP)
- **Auth:** JWT (access 30min / refresh 7 days) + OAuth (Google & Apple)
- **Real-time:** WebSocket with team-based subscriptions
- **Deployment:** Docker Compose, Google Cloud Run

## Commands

### Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head                          # apply migrations
uvicorn app.main:app --reload --port 8000     # dev server
pytest                                         # run all tests
pytest tests/test_auth.py                      # single test file
pytest tests/test_auth.py::test_login -v       # single test
pytest --cov=app                               # with coverage
```

### Frontend
```bash
cd frontend
npm install
npm run dev        # Vite dev server on port 3000
npm run build      # production build
npm run lint       # ESLint
npm run preview    # preview production build
```

### Docker
```bash
docker-compose up --build                        # full stack (frontend on :80, backend on :8000)
docker-compose --profile dev up frontend-dev     # Vite dev server on :3000 instead of nginx
```

### Database Migrations
```bash
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1
```

## Architecture

### Backend (`backend/app/`)

Follows a **Model → Schema → Endpoint** pattern per entity:

```
models/       SQLAlchemy ORM models (11 tables)
schemas/      Pydantic request/response validation
api/v1/       FastAPI route handlers (13 endpoint modules)
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
components/   Layout (AppLayout, Header, Sidebar, MobileNav) + dev tools (DevRoleSwitcher)
store/        Zustand stores: authStore (auth state, UI state, notifications)
services/     api.ts (Axios client with JWT interceptor + token refresh) and mockApi.ts (dev fallback)
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

## Dev Mode

The frontend has a dev-only `DevRoleSwitcher` component with hardcoded demo users for quick role testing. Mock API (`mockApi.ts`) provides fallback data when the backend is unavailable. Both are tree-shaken from production builds.

**Demo accounts:** admin@handball.de/admin123, coach@handball.de/coach123, eltern@handball.de/parent123

## API Documentation

When backend is running: Swagger at `http://localhost:8000/api/v1/docs`, ReDoc at `http://localhost:8000/api/v1/redoc`.

## Environment Variables

Backend requires `.env` (copy from `.env.example`). Critical vars: `DATABASE_URL`, `SECRET_KEY` (fails on default), `GOOGLE_CLIENT_ID`, `APPLE_CLIENT_ID`. Frontend uses `VITE_API_URL`, `VITE_GOOGLE_CLIENT_ID`, and `VITE_APPLE_CLIENT_ID`.
