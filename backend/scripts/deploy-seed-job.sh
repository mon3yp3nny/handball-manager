#!/usr/bin/env bash
#
# Deploy (or re-deploy) the `handball-seed` Cloud Run Job, then optionally
# execute it. The Job reuses the already-built handball-backend image and
# runs `python scripts/setup_data.py` against the prod Cloud SQL instance.
#
# Use this when sample/test users need to be (re-)seeded on prod —
# setup_data.py is idempotent, so re-running won't duplicate or clobber
# existing accounts.
#
# Prereqs:
#   - gcloud installed and authenticated against `handball-club-manager`
#   - Roles needed:
#       roles/run.developer        (deploy the Job)
#       roles/run.invoker          (execute the Job)
#       roles/iam.serviceAccountUser (act-as the runtime SA below)
#
# Usage:
#   ./backend/scripts/deploy-seed-job.sh deploy        # create/update only
#   ./backend/scripts/deploy-seed-job.sh execute       # run an existing Job
#   ./backend/scripts/deploy-seed-job.sh deploy-and-run
#
set -euo pipefail

PROJECT_ID="handball-club-manager"
REGION="europe-west1"
JOB_NAME="handball-seed"
BACKEND_IMAGE="gcr.io/${PROJECT_ID}/handball-backend:latest"
CLOUDSQL_INSTANCE="${PROJECT_ID}:${REGION}:handball-db"

# Runtime service account — should match (or be a subset of) the SA the
# handball-backend service runs as, so it has Cloud SQL Client + access
# to the same Secret Manager secrets. Override with:
#   RUNTIME_SA=my-other-sa@... ./deploy-seed-job.sh deploy
RUNTIME_SA="${RUNTIME_SA:-}"

# Secret Manager references the Job needs. The backend service is
# already configured with these — re-declare them here so the Job has
# the same access (least-privilege: list ONLY what setup_data.py needs).
#
# setup_data.py imports app.core.config which fails fast if SECRET_KEY
# is the placeholder default, so SECRET_KEY is mandatory. DATABASE_URL
# is what the script actually uses to connect.
#
# Format: ENV_VAR=secret-name:version (matching `gcloud run services
# update --set-secrets ...` syntax). Set these via env or edit inline:
SECRETS="${SECRETS:-DATABASE_URL=database-url:latest,SECRET_KEY=secret-key:latest}"

# Plain env vars (non-secret). Add any others the backend reads at
# startup that setup_data.py's imports also touch — empty by default.
ENV_VARS="${ENV_VARS:-}"

deploy_job() {
  echo "→ Deploying Cloud Run Job '${JOB_NAME}' (image: ${BACKEND_IMAGE})"

  local sa_flag=()
  if [[ -n "${RUNTIME_SA}" ]]; then
    sa_flag=(--service-account "${RUNTIME_SA}")
  fi

  local env_flag=()
  if [[ -n "${ENV_VARS}" ]]; then
    env_flag=(--set-env-vars "${ENV_VARS}")
  fi

  # `gcloud run jobs deploy` is create-or-update — safe to re-run.
  gcloud run jobs deploy "${JOB_NAME}" \
    --project="${PROJECT_ID}" \
    --region="${REGION}" \
    --image="${BACKEND_IMAGE}" \
    --set-cloudsql-instances="${CLOUDSQL_INSTANCE}" \
    --set-secrets="${SECRETS}" \
    "${env_flag[@]}" \
    "${sa_flag[@]}" \
    --command="python" \
    --args="/app/scripts/setup_data.py" \
    --max-retries=1 \
    --task-timeout=300s \
    --memory=512Mi \
    --cpu=1

  echo "✓ Job '${JOB_NAME}' deployed."
}

execute_job() {
  echo "→ Executing Cloud Run Job '${JOB_NAME}' (this connects to prod Cloud SQL)"
  gcloud run jobs execute "${JOB_NAME}" \
    --project="${PROJECT_ID}" \
    --region="${REGION}" \
    --wait
  echo "✓ Execution finished. Inspect logs with:"
  echo "    gcloud run jobs executions list --job=${JOB_NAME} --project=${PROJECT_ID} --region=${REGION}"
}

case "${1:-deploy}" in
  deploy)         deploy_job ;;
  execute)        execute_job ;;
  deploy-and-run) deploy_job && execute_job ;;
  *)
    echo "usage: $0 {deploy|execute|deploy-and-run}" >&2
    exit 2
    ;;
esac
