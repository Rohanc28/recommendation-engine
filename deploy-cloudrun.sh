#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Recommendation Engine — Cloud Run free-tier deployment script
#
# Requirements:
#   gcloud CLI authenticated  (gcloud auth login)
#   Docker daemon running
#   gcloud config set project <PROJECT_ID>
#
# Free-tier limits:
#   2 million requests/month, 360,000 vCPU-s/month, 180,000 GiB-s/month
#   1 x minimum-instance keeps the SQLite DB alive between requests
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

PROJECT_ID=$(gcloud config get-value project)
REGION=${REGION:-us-central1}
SERVICE_NAME=${SERVICE_NAME:-rec-engine-backend}
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "▶ Project : ${PROJECT_ID}"
echo "▶ Region  : ${REGION}"
echo "▶ Image   : ${IMAGE}"
echo ""

# ── 1. Build & push ───────────────────────────────────────────────────────────
echo "── Building Docker image (CPU-only torch, model baked in)…"
docker build -t "${IMAGE}:latest" ./backend

echo "── Pushing to Container Registry…"
docker push "${IMAGE}:latest"

# ── 2. Deploy to Cloud Run ────────────────────────────────────────────────────
echo "── Deploying to Cloud Run…"
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE}:latest" \
  --region "${REGION}" \
  --platform managed \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --concurrency 80 \
  --min-instances 1 \
  --max-instances 3 \
  --timeout 60 \
  --set-env-vars "DEMO_MODE=true" \
  --set-env-vars "DATABASE_URL=sqlite+aiosqlite:///./movies.db" \
  --set-env-vars "SECRET_KEY=${SECRET_KEY:-CHANGE_ME_BEFORE_DEPLOY_32chars!!}" \
  --set-env-vars "CORS_ORIGINS=[\"${FRONTEND_URL:-https://recommendation-engine.vercel.app}\"]"

SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
  --region "${REGION}" \
  --format "value(status.url)")

echo ""
echo "✅ Backend deployed: ${SERVICE_URL}"
echo ""
echo "Next steps:"
echo "  1. Set VITE_API_URL=${SERVICE_URL} in your Vercel project env vars"
echo "  2. cd frontend && vercel --prod"
echo ""
echo "Note: SQLite lives inside the container."
echo "  min-instances=1 keeps it alive; data resets on re-deploy."
echo "  For persistence: mount a GCS bucket volume or switch to Cloud SQL."
