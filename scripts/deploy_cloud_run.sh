#!/usr/bin/env bash
# ==============================================================================
# TradeSense AI — Google Cloud Run Deployment Script
# Startup Buildathon India 2026 Submission
# Region: asia-south1 (Mumbai)
# ==============================================================================

set -euo pipefail

# Configuration
SERVICE_NAME="tradesense-backend"
REGION="${GCP_REGION:-asia-south1}"
PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null || echo "")}"

echo "============================================================"
echo "🚀 TradeSense AI — Deploying to Google Cloud Run ($REGION)"
echo "============================================================"

if [ -z "$PROJECT_ID" ]; then
  echo "❌ Error: GCP_PROJECT_ID is not set. Please set GCP_PROJECT_ID or run: gcloud config set project <PROJECT_ID>"
  exit 1
fi

echo "🔹 Active GCP Project: $PROJECT_ID"
echo "🔹 Target Region: $REGION (Mumbai - Low Latency)"

# Step 1: Enable Necessary GCP APIs
echo "📦 Step 1: Enabling Google Cloud APIs..."
gcloud services enable \
    run.googleapis.com \
    aiplatform.googleapis.com \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com \
    memorystore.googleapis.com \
    --project="$PROJECT_ID"

# Step 2: Build and Tag Container with Cloud Build
IMAGE_TAG="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"
echo "🔨 Step 2: Building container image via Cloud Build: $IMAGE_TAG"
gcloud builds submit --tag "$IMAGE_TAG" -f backend/Dockerfile .

# Step 3: Deploy to Google Cloud Run
echo "🚀 Step 3: Deploying service to Google Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
    --image="$IMAGE_TAG" \
    --platform=managed \
    --region="$REGION" \
    --project="$PROJECT_ID" \
    --memory=1Gi \
    --cpu=1 \
    --min-instances=0 \
    --max-instances=100 \
    --concurrency=80 \
    --timeout=300 \
    --allow-unauthenticated \
    --set-env-vars="APP_ENV=production,GCP_REGION=${REGION},GCP_PROJECT_ID=${PROJECT_ID}"

# Step 4: Display Service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --platform=managed --region="$REGION" --format='value(status.url)')
echo ""
echo "============================================================"
echo "✅ TradeSense AI Backend Successfully Deployed!"
echo "🌐 Live Production URL: $SERVICE_URL"
echo "📊 Interactive Dashboard: $SERVICE_URL/"
echo "📖 Swagger API Docs: $SERVICE_URL/docs"
echo "============================================================"
