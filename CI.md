# CI/CD — Cloud Build

This repo ships a Cloud Build pipeline (`cloudbuild.yaml`) that runs the
backend test suite, builds both Docker images, pushes them to GCR, and
deploys to Cloud Run on every push to `main`.

> **GitHub Issue:** [#57](https://github.com/mon3yp3nny/handball-manager/issues/57)
> **Project:** `handball-club-manager` (`europe-west1`)
> **Services:** `handball-backend`, `handball-frontend`

## Pipeline at a glance

```
            ┌─────────────────┐
            │ backend-tests   │   (pytest gate — must pass)
            └────────┬────────┘
        ┌────────────┴────────────┐
        ▼                         ▼
┌──────────────┐          ┌──────────────┐
│ backend-build│          │ frontend-build│   (parallel)
└──────┬───────┘          └──────┬───────┘
       ▼                         ▼
┌──────────────┐          ┌──────────────┐
│ backend-push │          │ frontend-push│
└──────┬───────┘          └──────┬───────┘
       ▼                         ▼
┌──────────────┐          ┌──────────────┐
│deploy-backend│          │deploy-frontend│
└──────────────┘          └──────────────┘
```

Each image gets two tags:
- `:$SHORT_SHA` — immutable, used by the deploy step. Rollback = redeploy a prior SHA.
- `:latest` — for manual `gcloud run deploy --image .../latest` if you ever need it.

A red pytest gate stops the whole pipeline — broken `main` never reaches Cloud Run.

## One-time setup

### 1. Service account roles

The Cloud Build SA (`218596927281@cloudbuild.gserviceaccount.com`) needs:

| Role | Why |
|---|---|
| `roles/cloudbuild.builds.builder` | Default. Build + push images. |
| `roles/run.admin` | Call `gcloud run deploy`. |
| `roles/iam.serviceAccountUser` | Act as the Cloud Run runtime SA. |

Grant the two extra roles once:

```bash
gcloud projects add-iam-policy-binding handball-club-manager \
  --member="serviceAccount:218596927281@cloudbuild.gserviceaccount.com" \
  --role="roles/run.admin" --condition=None

gcloud projects add-iam-policy-binding handball-club-manager \
  --member="serviceAccount:218596927281@cloudbuild.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser" --condition=None
```

### 2. Connect the GitHub repo

Cloud Build's GitHub App needs to be installed on the repo before triggers
can be created. This is a one-time interactive step:

1. Open [Cloud Build → Triggers](https://console.cloud.google.com/cloud-build/triggers?project=handball-club-manager)
2. Click **Connect Repository** → **GitHub (Cloud Build GitHub App)**
3. Authenticate, pick `mon3yp3nny/handball-manager`, finish.

### 3. Create the trigger

Once the repo is connected:

```bash
gcloud builds triggers create github \
  --name=handball-main \
  --repo-name=handball-manager \
  --repo-owner=mon3yp3nny \
  --branch-pattern=^main$ \
  --build-config=cloudbuild.yaml \
  --project=handball-club-manager
```

From now on, every push to `main` triggers the full pipeline.

## Running it manually

For one-off deploys or local validation of YAML changes:

```bash
SHA=$(git rev-parse --short HEAD)
gcloud builds submit \
  --project=handball-club-manager \
  --config=cloudbuild.yaml \
  --substitutions=SHORT_SHA=$SHA \
  .
```

(`$SHORT_SHA` is auto-populated by trigger-driven builds; manual `submit`s
have to pass it.)

## Rollback

The images are SHA-tagged, so rollback is a single deploy:

```bash
# Roll handball-backend back to commit abc1234
gcloud run deploy handball-backend \
  --image=gcr.io/handball-club-manager/handball-backend:abc1234 \
  --region=europe-west1 --platform=managed

# Same for frontend
gcloud run deploy handball-frontend \
  --image=gcr.io/handball-club-manager/handball-frontend:abc1234 \
  --region=europe-west1 --platform=managed
```

The old `deploy.sh` script still works for ad-hoc local deploys but is no
longer the primary path — CI is.

## What runs in the test gate

`backend-tests` runs `pytest --no-cov -q` against the in-memory SQLite
fixture in `conftest.py`. No DB sidecar, no fixtures plumbing, no
secrets. Currently ~243 tests, ~30 seconds.

Frontend tests aren't gated yet — [#55](https://github.com/mon3yp3nny/handball-manager/issues/55)
will add Vitest and we'll insert a `frontend-tests` step ahead of
`frontend-build` with the same `waitFor: ['-']` semantics.

## Watching a build

- Console: [Cloud Build → History](https://console.cloud.google.com/cloud-build/builds?project=handball-club-manager)
- CLI: `gcloud builds list --project=handball-club-manager --limit=5`
- Logs for a specific build: `gcloud builds log <BUILD_ID> --project=handball-club-manager`
