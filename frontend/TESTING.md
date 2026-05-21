# Frontend Testing

Unit + component tests run on **Vitest** + **happy-dom** + **React Testing Library**.
End-to-end tests are separate, run on Playwright (see `e2e/`).

> **GitHub Issue:** [#55](https://github.com/mon3yp3nny/handball-manager/issues/55)

## Quick start

```bash
cd frontend
npm install
npm test              # one-shot run (CI mode)
npm run test:watch    # interactive watcher
npm run test:coverage # one-shot run + coverage report
```

## Node version

The project pins **Node 22 LTS** via `.nvmrc` and `engines`. Vitest 4
hangs at startup on Node 25 — happy-dom and jsdom both fail to
initialize under the worker pool. If `nvm` is installed:

```bash
nvm use   # picks Node 22 from .nvmrc
```

Without nvm, install via Homebrew:

```bash
brew install node@22
export PATH="/opt/homebrew/opt/node@22/bin:$PATH"
```

Node 20 LTS also works (CI uses 22, locally either is fine).

## Layout

```
frontend/src/
├── test/
│   └── setup.ts                     # jest-dom matchers + jsdom polyfills
├── lib/__tests__/
│   └── sentry.test.ts               # Sentry wrapper contract (#64)
└── components/__tests__/
    └── ErrorBoundary.test.tsx       # last-line-of-defense for the SPA
```

Tests live next to the code they cover, in a `__tests__/` sibling
folder. This keeps the import paths short (`../sentry` from inside
the test file) and means deleting a feature deletes its tests with it.

## What's currently covered

| File | What it asserts |
|---|---|
| `lib/sentry.test.ts` | `initSentry` no-op without DSN, 4xx error filter, header + body scrubbing, `setSentryUser` PII contract |
| `components/ErrorBoundary.test.tsx` | renders children, fallback UI (full + inline), `resetKey` auto-clear, manual reset button, `captureError` called with boundary name + componentStack |

27 tests, ~380 ms locally.

## Conventions

- **Globals are enabled** (`globals: true` in vitest config) — use
  `describe` / `it` / `expect` / `vi` without imports.
- **Setup file runs once per file** — jsdom doesn't ship `matchMedia`,
  `IntersectionObserver`, or `scrollTo` and many components call those
  on mount. The setup file stubs them.
- **Use `vi.mock()` for sibling modules** — e.g. tests for components
  that import `@/lib/sentry` mock that wrapper rather than touching the
  real SDK.
- **DOM cleans up between tests** via `cleanup()` in `afterEach`.

## Adding a test

1. Create `src/<path>/__tests__/<name>.test.tsx` next to the file under
   test.
2. Import only from `vitest` and `@testing-library/*` — no Jest-specific
   APIs.
3. Match the existing tests' tone: a short doc-comment at the top
   explaining what's being asserted and why, then `describe` blocks per
   behavior.

## Coverage

```bash
npm run test:coverage
open coverage/index.html
```

Coverage isn't enforced as a CI gate yet. The plan is to set a low
floor (~30 %) once a few more critical units are covered (api
interceptor, useAuth, route guard), then ratchet up.

## CI

The pipeline runs `frontend-tests` ahead of `frontend-build` (in
parallel with `backend-tests`), gated on the result. See `cloudbuild.yaml`
+ `CI.md`. The CI image is `node:22-slim`.
