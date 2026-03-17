# Structure

## Directory Layout

```
handball-manager/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI app entry point
│   │   ├── api/v1/
│   │   │   ├── api.py                 # Router aggregation
│   │   │   └── endpoints/             # 13 route modules
│   │   │       ├── auth.py            # Login, register, refresh
│   │   │       ├── oauth.py           # Google/Apple OAuth
│   │   │       ├── teams.py           # Team CRUD
│   │   │       ├── players.py         # Player CRUD
│   │   │       ├── games.py           # Game CRUD
│   │   │       ├── events.py          # Event CRUD
│   │   │       ├── attendance.py      # Attendance tracking
│   │   │       ├── news.py            # News/announcements
│   │   │       ├── invitations.py     # Team invitations
│   │   │       ├── parents.py         # Parent-child management
│   │   │       ├── users.py           # User management
│   │   │       └── health.py          # Health check
│   │   ├── models/                    # 11 SQLAlchemy ORM models
│   │   ├── schemas/                   # Pydantic request/response schemas
│   │   ├── core/                      # Config, security, permissions, OAuth, DI
│   │   ├── services/                  # Business logic (oauth, email)
│   │   ├── db/                        # Database session & base
│   │   └── websocket/                 # ConnectionManager for real-time
│   ├── alembic/                       # Migration scripts
│   ├── tests/                         # Pytest test files
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .dockerignore
├── frontend/
│   ├── src/
│   │   ├── main.tsx                   # React entry point
│   │   ├── App.tsx                    # Router & protected routes
│   │   ├── pages/                     # 14 page components
│   │   │   ├── auth/                  # LoginPage
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── Teams/
│   │   │   ├── Players/
│   │   │   ├── Games/
│   │   │   ├── Events/
│   │   │   ├── Attendance/
│   │   │   ├── News/
│   │   │   ├── Family/               # ParentDashboard
│   │   │   ├── CalendarPage.tsx
│   │   │   ├── ProfilePage.tsx
│   │   │   └── NotFoundPage.tsx
│   │   ├── components/
│   │   │   ├── layout/               # AppLayout, Header, Sidebar, MobileNav
│   │   │   ├── dev/                   # DevRoleSwitcher
│   │   │   └── ErrorBoundary.tsx
│   │   ├── store/                     # Zustand (authStore)
│   │   ├── services/                  # api.ts, mockApi.ts
│   │   ├── hooks/                     # useAuth, useWebSocket, useParent
│   │   └── types/                     # TypeScript domain interfaces
│   ├── public/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── Dockerfile
│   └── .dockerignore
├── docker-compose.yml
├── CLAUDE.md
└── README.md
```

## Naming Conventions

| Context | Convention | Example |
|---------|-----------|---------|
| Backend files | snake_case | `oauth_account.py`, `parent_child.py` |
| Backend classes | PascalCase | `ParentChild`, `OAuthAccount` |
| Backend functions | snake_case | `get_current_user`, `require_admin` |
| Frontend files (pages) | PascalCase | `DashboardPage.tsx`, `CalendarPage.tsx` |
| Frontend files (utils) | camelCase | `api.ts`, `mockApi.ts` |
| Frontend components | PascalCase | `<AppLayout>`, `<ProtectedRoute>` |
| Frontend hooks | camelCase with `use` prefix | `useAuth`, `useWebSocket` |
| API routes | kebab-case / plural nouns | `/api/v1/teams`, `/api/v1/auth/login` |
| Database tables | snake_case plural | `users`, `parent_children` |

## Where to Add New Code

| What | Where |
|------|-------|
| New entity | `backend/app/models/`, `schemas/`, `api/v1/endpoints/`, add router in `api.py` |
| New page | `frontend/src/pages/NewFeature/`, add route in `App.tsx` |
| New shared component | `frontend/src/components/` |
| New hook | `frontend/src/hooks/` |
| New backend service | `backend/app/services/` |
| New migration | `cd backend && alembic revision --autogenerate -m "description"` |
| New permission rule | `backend/app/core/permissions.py` |
