#!/bin/bash

# Deploy to Cloud Run Script
# Usage: ./deploy.sh

set -e

# Configuration
PROJECT_ID="comic-ai-agent-470309"
REGION="asia-northeast1"
SERVICE_NAME="manga-backend"
IMAGE_NAME="manga-backend"
REPOSITORY="manga-service"

echo "🚀 Deploying AI Manga Generation Service to Cloud Run..."
echo "   Project: $PROJECT_ID"
echo "   Region: $REGION"
echo "   Service: $SERVICE_NAME"

# Check if logged in to gcloud
echo "📝 Checking GCloud authentication..."
if ! gcloud auth list --format="value(account)" | grep -q .; then
    echo "❌ Not logged in to gcloud. Please run: gcloud auth login"
    exit 1
fi

# Set project
gcloud config set project $PROJECT_ID

# Build and push Docker image
echo "🔨 Building Docker image..."
IMAGE_TAG="$REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/$IMAGE_NAME:latest"

docker build -t $IMAGE_TAG .

echo "📤 Pushing image to Artifact Registry..."
docker push $IMAGE_TAG

# Deploy to Cloud Run
echo "🌐 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image=$IMAGE_TAG \
    --region=$REGION \
    --platform=managed \
    --allow-unauthenticated \
    --port=8000 \
    --memory=2Gi \
    --cpu=2 \
    --min-instances=1 \
    --max-instances=10 \
    --timeout=60 \
    --concurrency=100 \
    --set-env-vars="ENV=production,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,FIREBASE_PROJECT_ID=$PROJECT_ID" \
    --project=$PROJECT_ID

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --format='value(status.url)' \
    --project=$PROJECT_ID)

echo "✅ Deployment complete!"
echo "🔗 Service URL: $SERVICE_URL"
echo ""
echo "📋 Next steps:"
echo "   1. Update frontend environment with: $SERVICE_URL"
echo "   2. Configure Cloud SQL if using PostgreSQL"
echo "   3. Set up Cloud CDN for static assets"
echo "   4. Configure monitoring and alerts"