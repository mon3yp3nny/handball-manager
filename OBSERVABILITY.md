# Observability — Sentry

Backend (FastAPI) and frontend (React) both ship to a single Sentry
project. Errors carry the deploy's git SHA as the release tag, the
user's id + role as context, and have credentials scrubbed before
they leave the box.

> **GitHub Issue:** [#64](https://github.com/mon3yp3nny/handball-manager/issues/64)

## What gets captured

| | Captured | Filtered out |
|---|---|---|
| **Backend** | unhandled exceptions, 5xx HTTPExceptions, 10% perf traces | 401/403/404/422 HTTPExceptions (expected business outcomes) |
| **Frontend** | unhandled errors, ErrorBoundary catches, 10% perf traces | axios errors with 4xx status (validation, auth, not-found) |

## What gets scrubbed

Before any event leaves the process:

- **Headers:** `Authorization`, `Cookie`, `Set-Cookie`, `X-CSRF-Token`
- **Body fields:** `password`, `current_password`, `new_password`, `token`, `refresh_token`

## What's attached as user context

Only `user_id` and `role`. **Never** email, name, IP address. The whole
point of self-hosted handball stats is keeping member identities off
third-party services — Sentry gets enough to correlate errors to a
session, nothing more.

## One-time setup

### 1. Create a Sentry project

1. Sign up at [sentry.io](https://sentry.io) (free tier: 5K errors/month).
2. Create a project for `python-fastapi` and one for `react`. You can
   point both at the same project if you prefer a unified feed — the
   release tag uses the same SHA across services, so issues correlate
   either way.
3. Copy the DSN from each project's Settings → Client Keys (DSN).

### 2. Configure the backend DSN

Backend reads `SENTRY_DSN` from the Cloud Run env. Set it once:

```bash
gcloud run services update handball-backend \
  --region=europe-west1 \
  --update-env-vars="SENTRY_DSN=https://...@o0.ingest.sentry.io/0"
```

The CI deploy step writes `SENTRY_RELEASE=$SHORT_SHA` and
`SENTRY_ENVIRONMENT=production` on every push, so those don't need to
be set manually.

For local dev, leave `SENTRY_DSN` unset in your `.env` — the backend
is a no-op without it.

### 3. Configure the frontend DSN

The frontend DSN is a **build-time** value (Vite inlines it into the
bundle). Set it on the Cloud Build trigger:

```bash
gcloud builds triggers update handball-main \
  --update-substitutions=_VITE_SENTRY_DSN=https://...@o0.ingest.sentry.io/0
```

Every future push to `main` will bake the DSN into the bundle. For
local dev, leave `VITE_SENTRY_DSN` unset.

### 4. Alerts (optional)

In the Sentry UI: **Alerts → Create Alert Rule**. Recommended starting
config:

- *Trigger:* a new issue is created
- *Filter:* `environment` is `production`
- *Action:* send email to your team (or Slack, with the Slack integration)

## Architecture notes

### Backend wiring (`app/core/observability.py`)

- `init_sentry()` runs once in `app/main.py` before `FastAPI()`
  construction — required so the Sentry integration can wrap the
  ASGI app.
- `set_user_context(user_id, role)` is called from `get_current_user`,
  so every authenticated request has identity attached to the scope.
- `_before_send()` filters expected 4xx HTTPExceptions and scrubs auth
  headers + credential body fields.

### Frontend wiring (`src/lib/sentry.ts`)

- `initSentry()` runs in `main.tsx` before `ReactDOM.render`.
- `setSentryUser()` / `clearSentryUser()` are wired through `useAuth`
  on login / logout / refresh-on-mount.
- `ErrorBoundary.componentDidCatch` calls `captureError` with the
  component stack as `extra`.

### Source maps

Not uploaded yet — the deployed JS will show minified stack traces in
Sentry. To turn this on, add `@sentry/vite-plugin` to the frontend
build with a `SENTRY_AUTH_TOKEN` secret. Tracked separately in #64
follow-up.

## Verifying it works

After setting the backend DSN, hit a 500 manually:

```bash
# Force an error (replace TOKEN with a valid one). The endpoint
# doesn't exist, but a real test would be to remove a critical env
# var temporarily and watch for the startup failure.
curl https://handball-backend-218596927281.europe-west1.run.app/api/v1/dashboard/widgets
```

Within ~30s the event should appear in the Sentry project, tagged with
`release=<commit SHA>` and `environment=production`.
