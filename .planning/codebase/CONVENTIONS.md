# Conventions

## Backend (Python / FastAPI)

### Code Style
- Python 3.11 standard library conventions
- snake_case for functions, variables, file names
- PascalCase for classes (models, schemas)
- Type hints used in function signatures (Pydantic enforces schema types)

### Import Organization
```python
# 1. Standard library
from datetime import datetime, timedelta
from typing import List, Optional

# 2. Third-party
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

# 3. Local
from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.user import UserResponse
```

### Endpoint Pattern
Every endpoint module follows this structure:
```python
router = APIRouter()

@router.get("/", response_model=List[SomeSchema])
def list_items(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # RBAC check via decorator or inline role check
    # Query with role-based filtering
    # Return Pydantic schema
```

### Error Handling
- `HTTPException` with status codes (400, 401, 403, 404)
- No custom exception classes — direct raises in endpoint handlers
- Auth failures: 401 for unauthenticated, 403 for unauthorized

### RBAC Decorators
```python
from app.core.permissions import require_roles

@router.post("/")
@require_roles("admin", "coach")
def create_item(...):
```

### Database Patterns
- `db.query(Model).filter(...)` pattern (SQLAlchemy 1.x query style on 2.x)
- `db.add()` / `db.commit()` / `db.refresh()` for writes
- No eager loading configured — relationships loaded lazily

## Frontend (TypeScript / React)

### Code Style
- ESLint with zero-warnings policy (`--max-warnings 0`)
- React hooks plugin for rules of hooks enforcement
- React Refresh plugin for fast HMR

### Component Pattern
```tsx
// Functional components with hooks
const PageName: React.FC = () => {
  const { user } = useAuth();
  const { data, isLoading } = useQuery({...});

  if (isLoading) return <LoadingSpinner />;

  return (
    <div className="tailwind classes">
      {/* JSX */}
    </div>
  );
};

export default PageName;
```

### State Management
- **Zustand** for client state (auth, UI, notifications) — persisted to localStorage
- **TanStack Query** for server state (API data fetching/caching)
- No Redux, no Context API for state

### API Calls
```tsx
// All API calls go through services/api.ts
import api from '@/services/api';

// Axios instance with JWT interceptor
// Auto-refreshes on 401
```

### Notifications
- `react-hot-toast` for user-facing messages
- Pattern: `toast.success("Saved!")`, `toast.error("Failed")`

### German UI Labels
Domain terms use German labels:
- Positions: Torwart, Rückraum Links, etc.
- Attendance: Anwesend, Abwesend, Entschuldigt
- Event types: Training, Spiel, Sonstiges
- Roles displayed in German in the UI
