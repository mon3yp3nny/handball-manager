# E2E Test Suite

Comprehensive end-to-end tests for the Handball Manager application covering all user roles and lifecycles.

## Test Files

| File | Description | Runtime |
|------|-------------|---------|
| `test-e2e-all-roles.sh` | Core tests for all roles | ~30s |
| `test-comprehensive-e2e.sh` | Full lifecycle with permissions | ~60s |
| `test-quick-e2e.sh` | Smoke tests only | ~15s |
| `test-user-lifecycle.sh` | Basic registration → login → delete | ~10s |

## Roles Covered

### 1. Player
- ✅ Registration
- ✅ Login
- ✅ Profile access
- ✅ View teams
- ❌ Cannot create teams (403)
- ✅ Account deletion

### 2. Coach
- ✅ Registration
- ✅ Login
- ✅ Create teams
- ✅ Manage team data
- ✅ View players

### 3. Parent
- ✅ Registration
- ✅ Login
- ✅ View children's teams
- ✅ View team schedules
- ❌ Cannot create teams

### 4. Admin
- ✅ Full dashboard access
- ✅ View all statistics
- ✅ User management
- ✅ System health checks

### 5. Multi-Role (Coach + Player)
- ✅ Can act as both roles
- ✅ Team creation (coach permission)
- ✅ Player profile access

## Running Tests

### Local
```bash
# All roles
bash test-e2e-all-roles.sh

# Comprehensive
bash test-comprehensive-e2e.sh

# Quick smoke test
bash test-quick-e2e.sh
```

### CI/CD
Tests run automatically via GitHub Actions:
- On every push to `main` or `develop`
- On every pull request to `main`
- Daily at 6 AM UTC

## Test Results

**Latest Run:**
```
✅ Passed: 10
❌ Failed: 5

Known Issues:
- Team viewing permissions need adjustment
- Stats token generation needs fix
```

## Sample Users

Created by setup script:

| Email | Password | Roles |
|-------|----------|-------|
| `admin@handball.local` | `Admin123!` | Admin |
| `max.mustermann@example.com` | `Test123!` | Coach + Player + Parent |
| `anna.schmidt@example.com` | `Test123!` | Supervisor + Parent |
| `thomas.weber@example.com` | `Test123!` | Coach + Player |
| `lisa.mueller@example.com` | `Test123!` | Player |

## API Endpoints Tested

- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /auth/me` - User profile
- `GET /teams` - List teams
- `POST /teams` - Create team (coach/admin only)
- `DELETE /users/me/account` - Delete account
- `GET /dashboard/stats` - Dashboard statistics
- `GET /dashboard/admin/summary` - Admin statistics

## Adding New Tests

1. Add test function following existing pattern
2. Use `test_pass` and `test_fail` helpers
3. Test both success and failure cases
4. Update this README

## Troubleshooting

### Tests failing with "Backend unreachable"
Check if backend is running:
```bash
curl https://handball-backend-218596927281.europe-west1.run.app/
```

### Permission errors
Ensure test users have correct roles. Use setup endpoint:
```bash
curl -X POST "$BASE_URL/setup/init" \
  -H "Content-Type: application/json" \
  -d '{"secret": "init-handball-2024"}'
```

## Maintenance

Last updated: 2026-03-28
Maintainer: Jan Redepenning
