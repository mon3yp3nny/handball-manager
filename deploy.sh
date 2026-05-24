#!/bin/bash
# Deploy script for Handball Manager to Google Cloud Run

set -euo pipefail

PROJECT_ID="handball-club-manager"
REGION="europe-west1"
BACKEND_IMAGE="gcr.io/${PROJECT_ID}/handball-backend"

echo "🔧 Building and deploying Handball Manager..."
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo ""

# Build and push backend
echo "📦 Building backend..."
cd backend
gcloud builds submit --project ${PROJECT_ID} --tag ${BACKEND_IMAGE}:latest .
cd ..

echo "🚀 Deploying backend to Cloud Run..."
# NOTE: Env vars (DATABASE_URL, SECRET_KEY, FRONTEND_URL, BACKEND_CORS_ORIGINS)
# are configured on the Cloud Run service and persist across revisions. Do NOT
# pass --set-env-vars here — it would replace the entire env and break auth/db.
# Manage env via:  gcloud run services update handball-backend --update-env-vars KEY=VALUE
gcloud run deploy handball-backend \
  --image ${BACKEND_IMAGE}:latest \
  --region ${REGION} \
  --project ${PROJECT_ID} \
  --platform managed \
  --allow-unauthenticated \
  --add-cloudsql-instances ${PROJECT_ID}:${REGION}:handball-db \
  --max-instances 5 \
  --memory 512Mi \
  --cpu 1

# Build + deploy frontend via cloudbuild-frontend.yaml. It builds
# Dockerfile.cloudrun (nginx proxies /api + /ws so the auth cookie stays
# first-party, VITE_API_URL=/api/v1) and deploys to Cloud Run in one step.
# Do NOT build the frontend with `--tag` / the default Dockerfile — that
# bakes a cross-origin API URL and re-breaks login.
echo "📦 Building + deploying frontend (same-origin)..."
gcloud builds submit --project ${PROJECT_ID} --config cloudbuild-frontend.yaml --region ${REGION} .

echo ""
echo "✅ Deployment complete!"
echo "Backend: https://handball-backend-218596927281.europe-west1.run.app"
echo "Frontend: https://handball-frontend-218596927281.europe-west1.run.app"
