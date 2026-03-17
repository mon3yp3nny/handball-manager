# Testing

## Backend Testing

### Framework
- **pytest** 7.4.3 with `pytest-asyncio` 0.21.1
- **httpx** 0.25.2 as async test client for FastAPI
- **pytest-cov** 4.1.0 for coverage reporting

### Configuration
- `backend/pytest.ini` — test discovery, async mode
- `backend/.coveragerc` — coverage config, omits `oauth`, `websocket`, `migrations`

### Structure
```
backend/tests/
├── conftest.py          # Fixtures: test DB, client, role-based users
├── test_auth.py         # Auth endpoints (login, register, refresh)
├── test_teams.py        # Team CRUD
├── test_players.py      # Player CRUD
├── test_games.py        # Game CRUD
├── test_events.py       # Event CRUD
├── test_attendance.py   # Attendance tracking
├── test_invitations.py  # Invitation flow
└── ...
```

### Patterns
- **Test classes** group related tests: `TestLogin`, `TestRefreshToken`, `TestRegister`
- **Fixtures** in `conftest.py` provide:
  - Test database session (isolated per test)
  - Pre-created users per role (admin, coach, supervisor, player, parent)
  - Test client with auth headers
- **Assertion style:** Direct assert statements, no assertion libraries

### Running
```bash
cd backend
pytest                              # all tests
pytest tests/test_auth.py           # single file
pytest tests/test_auth.py::TestLogin -v  # single class
pytest --cov=app                    # with coverage
```

## Frontend Testing

### Framework
- **Playwright** 1.58.2 for E2E tests
- No unit test framework (no Jest/Vitest configured)

### Structure
- E2E tests in `frontend/tests/` (Playwright)
- No component-level unit tests found

### Running
```bash
cd frontend
npx playwright test                    # all E2E tests
npx playwright test tests/foo.spec.ts  # single file
```

## Coverage Gaps

- No frontend unit tests (components, hooks, stores)
- OAuth flows excluded from backend coverage
- WebSocket manager excluded from backend coverage
- No integration tests for the full OAuth → JWT flow
- No load/performance tests
