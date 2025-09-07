#!/bin/bash

# Enhanced Production Deployment Script
# AI Manga Generation Service - Cloud Run Deployment

set -e

# Configuration
PROJECT_ID="comic-ai-agent-470309"
REGION="asia-northeast1"
SERVICE_NAME="manga-ai-backend"
IMAGE_NAME="backend"
REPOSITORY="manga-service"

echo "🚀 Deploying AI Manga Generation Service to Cloud Run (Production)..."
echo "   Project: $PROJECT_ID"
echo "   Region: $REGION"
echo "   Service: $SERVICE_NAME"

# Check if logged in
echo "📝 Checking GCloud authentication..."
if ! gcloud auth list --format="value(account)" | grep -q .; then
    echo "❌ Not logged in to gcloud. Please run: gcloud auth login"
    exit 1
fi

# Set project
gcloud config set project $PROJECT_ID

# Get latest image from Artifact Registry
echo "🔍 Getting latest image from Artifact Registry..."
IMAGE_TAG="asia-northeast1-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/$IMAGE_NAME:latest"

# Deploy to Cloud Run with production configuration
echo "🌐 Deploying to Cloud Run with production configuration..."
gcloud run deploy $SERVICE_NAME \
    --image=$IMAGE_TAG \
    --region=$REGION \
    --platform=managed \
    --allow-unauthenticated \
    --port=8000 \
    --memory=4Gi \
    --cpu=2 \
    --min-instances=1 \
    --max-instances=10 \
    --timeout=600 \
    --concurrency=50 \
    --cpu-boost \
    --execution-environment=gen2 \
    --vpc-connector=projects/$PROJECT_ID/locations/$REGION/connectors/manga-vpc-connector \
    --vpc-egress=private-ranges-only \
    --set-env-vars="ENV=production,DEBUG=false,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,VERTEXAI_LOCATION=$REGION,REDIS_HOST=10.37.0.3,REDIS_PORT=6379,LOG_LEVEL=INFO" \
    --set-secrets="DATABASE_URL=manga-db-url:latest,SECRET_KEY=manga-secret-key:latest" \
    --project=$PROJECT_ID

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --format='value(status.url)' \
    --project=$PROJECT_ID)

echo "✅ Production deployment complete!"
echo "🔗 Service URL: $SERVICE_URL"
echo ""
echo "📋 Verification steps:"
echo "   1. Health Check: curl $SERVICE_URL/health"
echo "   2. API Docs: $SERVICE_URL/docs"
echo "   3. Pipeline Info: $SERVICE_URL/api/v1/info"
echo ""
echo "📊 Monitoring:"
echo "   - Cloud Run Console: https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME"
echo "   - Logs: gcloud run logs tail $SERVICE_NAME --region=$REGION"