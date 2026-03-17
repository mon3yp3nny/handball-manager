# Concerns

## Tech Debt

### Missing Email Service
- `backend/app/services/email_service.py` is a mock — logs to console only
- Invitation flow, password reset, and notifications all depend on email
- **Impact:** Users can't receive invitations or password resets in production

### Demo Users in Codebase
- Hardcoded demo accounts (admin@handball.de, coach@handball.de, eltern@handball.de) in frontend `DevRoleSwitcher`
- Tree-shaken from production builds but exist in source
- **Impact:** Low risk, but credentials visible in repo

### N+1 Query Patterns
- Endpoint handlers query related models in loops (e.g., loading players per team, attendance per event)
- No eager loading (`joinedload`, `selectinload`) configured on relationships
- **Impact:** Performance degrades with data growth

### Unused Dependencies
- `redis==5.0.1` and `celery==5.3.6` installed but not actively used
- `moment==2.29.4` installed alongside `date-fns` (duplicate date libraries)
- **Impact:** Bloated dependencies, potential confusion

## Security Concerns

### Weak Authorization in Bulk Operations
- Some bulk endpoints may not fully validate per-item ownership
- Parent role filtering happens at query level but not consistently across all endpoints
- **Impact:** Potential data leakage between parents

### Plaintext Temporary Password
- When creating users via invitation, temporary passwords may be returned in API responses
- **Impact:** Credentials visible in network logs

### OAuth Token Revalidation
- After initial OAuth verification, backend trusts its own JWT — no periodic re-verification with provider
- **Impact:** Revoked Google/Apple accounts remain active until JWT expires

### WebSocket Session Invalidation
- No mechanism to invalidate WebSocket connections when JWT expires or user is deactivated
- **Impact:** Stale connections could receive data after access revocation

## Performance Concerns

### Parent-Child Query Inefficiency
- Parent endpoints filter through `ParentChild` join table for every request
- No database indexes observed on `parent_child.parent_id` / `parent_child.child_id`
- **Impact:** Slow queries as parent-child relationships grow

### Manual Response Construction
- Some endpoints manually build response dicts instead of using Pydantic `from_orm`
- **Impact:** Maintenance burden, potential inconsistencies

### No Database Connection Pooling Tuning
- Using default SQLAlchemy pool settings
- **Impact:** May need tuning under production load

## Fragile Areas

### ParentChild Model
- Used across multiple endpoints (`parents.py`, `attendance.py`, `teams.py`, `players.py`)
- Changes to this model have wide blast radius
- **Impact:** High coupling, changes require testing across many endpoints

### Attendance Dual-FK Pattern
- `Attendance` has two nullable FKs: `game_id` and `event_id` (one must be set)
- No database-level constraint enforcing exactly one is non-null
- **Impact:** Data integrity relies on application code

### Mock API Fallback
- Frontend `mockApi.ts` provides fallback data when backend is unavailable
- Dev mode detection in `authStore` can interfere with real API calls
- **Impact:** Bugs where dev mode state persists (recently fixed in commit `e3a05aa`)

### Activity Logging Scattered
- `UserActivity` logging happens inline in various endpoints
- No centralized middleware or decorator pattern
- **Impact:** Inconsistent audit trail, easy to forget logging in new endpoints

## Missing Critical Features

- **No password reset flow** (email service is mock)
- **No file/image upload** (player photos, team logos)
- **No pagination** on list endpoints
- **No search/filter** on most list endpoints
- **No audit log viewer** (UserActivity data exists but no UI)
- **No internationalization framework** (German strings hardcoded)
