#!/bin/bash
# Deploy script for Handball Manager to Google Cloud Run

set -e

PROJECT_ID="handball-club-manager"
REGION="europe-west1"
BACKEND_IMAGE="gcr.io/${PROJECT_ID}/handball-backend"
FRONTEND_IMAGE="gcr.io/${PROJECT_ID}/handball-frontend"

echo "🔧 Building and deploying Handball Manager..."
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo ""

# Build and push backend
echo "📦 Building backend..."
cd backend
gcloud builds submit --tag ${BACKEND_IMAGE}:latest .
cd ..

echo "🚀 Deploying backend to Cloud Run..."
gcloud run deploy handball-backend \
  --image ${BACKEND_IMAGE}:latest \
  --region ${REGION} \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars "DATABASE_URL=postgresql+psycopg2://USER:PASS@/DB?host=/cloudsql/PROJECT:REGION:INSTANCE" \
  --add-cloudsql-instances handball-club-manager:europe-west1:handball-db \
  --max-instances 5 \
  --memory 512Mi \
  --cpu 1

# Build and push frontend
echo "📦 Building frontend..."
cd frontend
gcloud builds submit --tag ${FRONTEND_IMAGE}:latest \
  --substitutions=_VITE_API_URL=https://handball-backend-218596927281.europe-west1.run.app,_VITE_GOOGLE_CLIENT_ID=,VITE_APPLE_CLIENT_ID= .
cd ..

echo "🚀 Deploying frontend to Cloud Run..."
gcloud run deploy handball-frontend \
  --image ${FRONTEND_IMAGE}:latest \
  --region ${REGION} \
  --platform managed \
  --allow-unauthenticated \
  --max-instances 5 \
  --memory 256Mi \
  --cpu 1

echo ""
echo "✅ Deployment complete!"
echo "Backend: https://handball-backend-218596927281.europe-west1.run.app"
echo "Frontend: https://handball-frontend-218596927281.europe-west1.run.app"
