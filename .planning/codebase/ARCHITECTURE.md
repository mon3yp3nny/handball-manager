# Architecture

## Pattern

**Backend:** Layered architecture following Model → Schema → Endpoint per entity. Business logic lives in endpoint handlers with some extraction to `services/`.

**Frontend:** Page-centric React SPA with centralized state (Zustand) and server state (TanStack Query). No component library — Tailwind utility classes directly.

## Backend Layers

```
┌─────────────────────────────────┐
│  API Layer (FastAPI routers)    │  backend/app/api/v1/endpoints/
│  - Route handlers               │  - 13 endpoint modules
│  - Request validation            │  - Pydantic schema binding
│  - RBAC enforcement              │  - require_roles() decorator
├─────────────────────────────────┤
│  Core Layer                     │  backend/app/core/
│  - Security (JWT)                │  - security.py
│  - Permissions (RBAC)            │  - permissions.py
│  - Config (Settings)             │  - config.py
│  - Dependencies (DI)             │  - deps.py
│  - OAuth providers               │  - oauth.py
│  - Rate limiting                 │  - rate_limiting.py
├─────────────────────────────────┤
│  Service Layer                  │  backend/app/services/
│  - OAuth service                 │  - oauth_service.py
│  - Email service (mock)          │  - email_service.py
├─────────────────────────────────┤
│  Schema Layer (Pydantic)        │  backend/app/schemas/
│  - Request/response models       │  - One file per entity
│  - Validation rules              │
├─────────────────────────────────┤
│  Model Layer (SQLAlchemy)       │  backend/app/models/
│  - ORM table definitions         │  - 11 model files
│  - Relationships                 │  - Soft delete on some
├─────────────────────────────────┤
│  Database Layer                 │  backend/app/db/
│  - Session factory               │  - session.py
│  - Connection pooling            │  - base.py
└─────────────────────────────────┘
```

## Frontend Layers

```
┌─────────────────────────────────┐
│  Pages                          │  frontend/src/pages/
│  - 14 page components            │  - Route-level views
│  - Data fetching                 │  - TanStack Query hooks
├─────────────────────────────────┤
│  Components                     │  frontend/src/components/
│  - Layout (AppLayout, Header,    │  - layout/
│    Sidebar, MobileNav)           │
│  - Dev tools (DevRoleSwitcher)   │  - dev/
│  - ErrorBoundary                 │
├─────────────────────────────────┤
│  State Management               │  frontend/src/store/
│  - authStore (Zustand)           │  - Auth, UI, notifications
│  - Persisted to localStorage     │
├─────────────────────────────────┤
│  Services                       │  frontend/src/services/
│  - api.ts (Axios + interceptors) │  - JWT refresh logic
│  - mockApi.ts (dev fallback)     │  - Tree-shaken in prod
├─────────────────────────────────┤
│  Hooks                          │  frontend/src/hooks/
│  - useAuth, useWebSocket         │  - useParent
├─────────────────────────────────┤
│  Types                          │  frontend/src/types/
│  - Domain entity interfaces      │  - Shared across app
└─────────────────────────────────┘
```

## Key Data Flows

### Authentication
1. User submits credentials → POST `/api/v1/auth/login`
2. Backend verifies password → returns access + refresh JWT
3. Frontend stores tokens in authStore (persisted to localStorage)
4. Axios interceptor attaches `Authorization: Bearer <token>` to all requests
5. On 401: interceptor auto-retries with refresh token

### OAuth
1. Frontend renders Google/Apple button → user authenticates with provider
2. Provider token sent to POST `/api/v1/oauth/{provider}`
3. Backend verifies token with provider API
4. Auto-creates or links User + OAuthAccount
5. Returns JWT + `needs_role_selection` flag
6. If new user: frontend calls POST `/api/v1/oauth/set-role`

### RBAC
1. Endpoint decorated with `require_roles()` from `backend/app/core/permissions.py`
2. Decorator checks `current_user.role` against allowed roles
3. Query-level filtering: database queries scope results by role (e.g., parents only see their children's teams)

### WebSocket
1. Client connects to `/ws`
2. Sends `{"token": "<JWT>"}` to authenticate
3. Sends `{"action": "subscribe_team", "team_id": N}`
4. Receives real-time broadcasts for subscribed teams

## Entry Points

- **Backend:** `backend/app/main.py` — FastAPI app creation, CORS, WebSocket endpoint, startup DB init
- **Frontend:** `frontend/src/main.tsx` → `App.tsx` — React Router with `<ProtectedRoute>` wrapper
- **API aggregation:** `backend/app/api/v1/api.py` — all routers under `/api/v1`
