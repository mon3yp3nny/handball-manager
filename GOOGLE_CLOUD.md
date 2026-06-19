# Google Cloud Runbook

How this project uses Google Cloud Platform (GCP): the resources, how to deploy,
how to manage config/secrets, and — importantly — how to control cost and put the
project on hold.

> **Current status (2026-06-20): the project is ON HOLD. All billable resources
> have been torn down to ~$0.** See [Project on hold / resume](#project-on-hold--resume)
> at the bottom to bring it back. The rest of this doc describes the deployment as
> it exists when running.

## Project facts

| Item | Value |
|------|-------|
| Project ID | `handball-club-manager` |
| Region | `europe-west1` |
| Billing account | `0126BF-646770-6E310A` |
| Owner account | `janredepenning12@googlemail.com` |
| Console | https://console.cloud.google.com/home/dashboard?project=handball-club-manager |

## What runs where

| App component | GCP service | Name |
|---------------|-------------|------|
| Backend (FastAPI) | Cloud Run service | `handball-backend` |
| Frontend (React/nginx) | Cloud Run service | `handball-frontend` |
| Database | Cloud SQL (PostgreSQL 15, `db-f1-micro`) | `handball-db` |
| Test-data seeding | Cloud Run Job | `handball-seed` |
| Container images | Container Registry (GCR) | `gcr.io/handball-club-manager/handball-{backend,frontend}` |
| Builds | Cloud Build | uses bucket `handball-club-manager_cloudbuild` |
| Secrets | Secret Manager | `database-url` / `db-password`, `secret-key` |

**Cost note:** Cloud Run scales to zero, so the two services and the job cost ~$0
when idle. **Cloud SQL is the only always-on resource** — `handball-db` billed 24/7
(~$8–10/mo) regardless of traffic. It is the entire bill in practice.

## Prerequisites (one-time)

```bash
# Install the gcloud CLI (https://cloud.google.com/sdk/docs/install), then:
gcloud auth login
gcloud config set project handball-club-manager
gcloud config set run/region europe-west1
```

## Deploying

### Full pipeline (recommended)
Builds + tests both images and deploys both services:
```bash
gcloud builds submit --config=cloudbuild.yaml --region=europe-west1 .
```

### Frontend only
The frontend **must** use the same-origin build (`cloudbuild-frontend.yaml`), which
builds `Dockerfile.cloudrun` so nginx proxies `/api` + `/ws` and the auth cookie stays
first-party. Do **not** build it with a plain `--tag` / default Dockerfile — that bakes a
cross-origin `VITE_API_URL` and breaks login.
```bash
gcloud builds submit --config=cloudbuild-frontend.yaml --region=europe-west1 .
```

### Backend only / convenience script
`./deploy.sh` builds the backend, deploys it (wiring `--add-cloudsql-instances` to
`handball-db`), then builds + deploys the frontend via `cloudbuild-frontend.yaml`.

## Configuration & secrets

- **Env vars live on the Cloud Run service** and persist across revisions. Do **not**
  pass `--set-env-vars` on a normal deploy — it replaces the entire env and breaks
  auth/DB. Update a single var with:
  ```bash
  gcloud run services update handball-backend --update-env-vars KEY=VALUE --region=europe-west1
  ```
- **Secrets** (`SECRET_KEY`, `DATABASE_URL`/DB password) are stored in Secret Manager
  and referenced via `--set-secrets`. `app.core.config` fails fast if `SECRET_KEY` is the
  placeholder default, so it is mandatory.
- Key vars: `DATABASE_URL`, `SECRET_KEY`, `GOOGLE_CLIENT_ID`, `APPLE_CLIENT_ID`,
  `AUTH_COOKIE_SAMESITE`/`AUTH_COOKIE_SECURE`, `BACKEND_CORS_ORIGINS`, `FRONTEND_URL`.
  Frontend (baked at build time): `VITE_API_URL=/api/v1`, `VITE_GOOGLE_CLIENT_ID`,
  `VITE_APPLE_CLIENT_ID`, `VITE_SENTRY_DSN`.

## Database migrations

`backend/scripts/start.sh` runs `alembic upgrade head` on container start, so migrations
apply automatically on the next backend deploy. Author one with:
```bash
cd backend && alembic revision --autogenerate -m "description"
```

## Seeding test data

`handball-seed` is a Cloud Run Job that reuses the backend image and runs
`scripts/setup_data.py` (idempotent) against prod Cloud SQL. Manage it with:
```bash
./backend/scripts/deploy-seed-job.sh deploy-and-run   # create/update + run
```

## Logs & monitoring

```bash
gcloud run services logs read handball-backend --region=europe-west1 --limit=100
```
Backend API docs (when deployed): Swagger `/api/v1/docs`, ReDoc `/api/v1/redoc`.
See `OBSERVABILITY.md` for Sentry / structured-logging details.

## Cost management

- **Idle by default:** Cloud Run scales to zero — no traffic, ~no cost. Cloud SQL does
  **not** scale to zero; it is the recurring charge.
- **Pause cheaply (keep data):** stop the DB instead of deleting it —
  `gcloud sql instances patch handball-db --activation-policy=NEVER`. Stops compute
  charges; only storage (~$1–2/mo) remains; resume with `--activation-policy=ALWAYS`.
- **Inspect billing:**
  ```bash
  gcloud billing projects describe handball-club-manager     # is billing linked?
  ```
  Cost/usage reports: https://console.cloud.google.com/billing/0126BF-646770-6E310A/reports?project=handball-club-manager
- **Budget alert (recommended):** set a low budget (e.g. €1) so any spend pings you —
  https://console.cloud.google.com/billing/0126BF-646770-6E310A/budgets

## Project on hold / resume

On **2026-06-20** the project was put on hold and torn down to ~$0. Deleted: both Cloud
Run services, the `handball-seed` job, the `handball-db` Cloud SQL instance (held test
data only — no backup kept), all GCR image digests, and the Cloud Build bucket contents.
Kept (negligible cost, eases resume): the two Secret Manager secrets.

**To bring it back** — everything is re-creatable from this repo:

1. **Recreate the database:**
   ```bash
   gcloud sql instances create handball-db \
     --database-version=POSTGRES_15 --tier=db-f1-micro --region=europe-west1
   gcloud sql databases create handball --instance=handball-db
   ```
   Re-point `DATABASE_URL` (Secret Manager) at the new instance if its connection
   details changed.
2. **Rebuild + redeploy** both services:
   ```bash
   gcloud builds submit --config=cloudbuild.yaml --region=europe-west1 .
   ```
   `start.sh` runs `alembic upgrade head` automatically on first boot.
3. **Re-seed test accounts:**
   ```bash
   ./backend/scripts/deploy-seed-job.sh deploy-and-run
   ```
