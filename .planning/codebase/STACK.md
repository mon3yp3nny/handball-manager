# Stack

## Languages & Runtimes

| Layer | Language | Version |
|-------|----------|---------|
| Backend | Python | 3.11 |
| Frontend | TypeScript | 5.3 |
| Database | SQL (PostgreSQL) | 15 |

## Backend Framework & Dependencies

**Framework:** FastAPI 0.104.1 with Uvicorn 0.24.0

**Core:**
- `sqlalchemy==2.0.23` — ORM
- `alembic==1.12.1` — database migrations
- `psycopg2-binary==2.9.9` — PostgreSQL driver
- `pydantic==2.5.2` / `pydantic-settings==2.1.0` — validation & config

**Auth:**
- `python-jose[cryptography]==3.3.0` — JWT encoding/decoding
- `passlib[bcrypt]==1.7.4` / `bcrypt==4.0.1` — password hashing
- `authlib==1.6.8` — OAuth client
- `google-auth==2.48.0` — Google token verification
- `PyJWT==2.8.0` — Apple token verification

**Infrastructure:**
- `redis==5.0.1` — cache (available but not actively used)
- `celery==5.3.6` — task queue (available but not actively used)
- `websockets==12.0` — real-time communication
- `slowapi==0.1.9` — rate limiting
- `python-json-logger==2.0.7` — structured logging

**Testing:**
- `pytest==7.4.3`, `pytest-asyncio==0.21.1`, `pytest-cov==4.1.0`
- `httpx==0.25.2` — async test client

## Frontend Framework & Dependencies

**Build:** Vite 5.0.8 with `@vitejs/plugin-react`

**Core:**
- `react==18.2.0` / `react-dom==18.2.0`
- `react-router-dom==6.20.1` — routing
- `zustand==4.4.7` — state management
- `@tanstack/react-query==5.13.4` — server state
- `axios==1.6.2` — HTTP client
- `react-hook-form==7.48.2` — form handling

**UI:**
- `tailwindcss==3.3.6` — utility CSS
- `lucide-react==0.294.0` — icons
- `react-hot-toast==2.4.1` — notifications
- `react-big-calendar==1.8.5` — calendar view
- `recharts==2.10.3` — charts/dashboards

**Date handling:** `date-fns==2.30.0`, `moment==2.29.4`

**Testing:** `@playwright/test==1.58.2` — E2E tests

## Configuration

**Backend:** Pydantic Settings reads from `.env` file. Key vars:
- `DATABASE_URL` — PostgreSQL connection string
- `SECRET_KEY` — JWT signing (fails on default value)
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` — Google OAuth
- `APPLE_CLIENT_ID` — Apple Sign-In
- `REDIS_URL` — optional Redis connection

**Frontend:** Vite env vars prefixed with `VITE_`:
- `VITE_API_URL` — backend API base URL
- `VITE_GOOGLE_CLIENT_ID` — Google OAuth client ID
- `VITE_APPLE_CLIENT_ID` — Apple Sign-In client ID

**Path alias:** `@` → `src/` (configured in `vite.config.ts` and `tsconfig.json`)

## Deployment

- **Docker Compose** for local/staging (PostgreSQL + backend + frontend)
- **Google Cloud Run** for production
- Frontend served via nginx in production, Vite dev server in development
- Backend with `--reload` in dev, standard Uvicorn in production
