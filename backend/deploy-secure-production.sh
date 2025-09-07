#!/bin/bash

# Secure Production Deployment Script for AI Manga Generation Service
# Google Cloud Hackathon - Enhanced Security & Performance

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Configuration
PROJECT_ID="comic-ai-agent-470309"
REGION="asia-northeast1"
SERVICE_NAME="manga-ai-backend"
REPOSITORY="manga-service"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log "🔍 Checking prerequisites..."
    
    # Check if gcloud is installed and authenticated
    if ! command -v gcloud &> /dev/null; then
        error "gcloud CLI is not installed"
    fi
    
    # Check authentication
    if ! gcloud auth list --format="value(account)" | grep -q .; then
        error "Not logged in to gcloud. Please run: gcloud auth login"
    fi
    
    # Check project access
    if ! gcloud projects describe "$PROJECT_ID" &>/dev/null; then
        error "Cannot access project $PROJECT_ID. Check permissions."
    fi
    
    # Set project
    gcloud config set project "$PROJECT_ID"
    
    info "✅ Prerequisites check passed"
}

# Enable required APIs
enable_apis() {
    log "🔧 Enabling required Google Cloud APIs..."
    
    apis=(
        "run.googleapis.com"
        "cloudbuild.googleapis.com"
        "artifactregistry.googleapis.com"
        "secretmanager.googleapis.com"
        "sqladmin.googleapis.com"
        "redis.googleapis.com"
        "aiplatform.googleapis.com"
        "compute.googleapis.com"
        "vpcaccess.googleapis.com"
    )
    
    for api in "${apis[@]}"; do
        if gcloud services list --enabled --filter="name:$api" --format="value(name)" | grep -q "$api"; then
            info "✅ $api already enabled"
        else
            info "🔄 Enabling $api..."
            gcloud services enable "$api"
        fi
    done
}

# Create Artifact Registry if not exists
setup_artifact_registry() {
    log "📦 Setting up Artifact Registry..."
    
    if gcloud artifacts repositories describe "$REPOSITORY" \
        --location="$REGION" &>/dev/null; then
        info "✅ Repository $REPOSITORY already exists"
    else
        info "🔄 Creating Artifact Registry repository..."
        gcloud artifacts repositories create "$REPOSITORY" \
            --repository-format=docker \
            --location="$REGION" \
            --description="AI Manga Generation Service container repository"
    fi
    
    # Configure Docker authentication
    gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet
}

# Setup secrets in Secret Manager
setup_secrets() {
    log "🔐 Setting up Secret Manager secrets..."
    
    # Generate secure secret key if not exists
    if ! gcloud secrets describe manga-secret-key &>/dev/null; then
        info "🔄 Creating secret key..."
        python3 -c "import secrets; print(secrets.token_urlsafe(32))" | \
        gcloud secrets create manga-secret-key --data-file=-
    else
        info "✅ Secret key already exists"
    fi
    
    # Check for database URL (needs manual setup)
    if ! gcloud secrets describe manga-db-url &>/dev/null; then
        warn "⚠️  Database URL secret not found!"
        warn "    Please create it manually with your Cloud SQL connection string:"
        warn "    echo 'postgresql+asyncpg://user:pass@host:5432/db' | gcloud secrets create manga-db-url --data-file=-"
    else
        info "✅ Database URL secret exists"
    fi
    
    # Check for Firebase credentials (needs manual setup)
    if ! gcloud secrets describe manga-firebase-creds &>/dev/null; then
        warn "⚠️  Firebase credentials secret not found!"
        warn "    Please create it manually with your service account JSON:"
        warn "    gcloud secrets create manga-firebase-creds --data-file=path/to/serviceAccountKey.json"
    else
        info "✅ Firebase credentials secret exists"
    fi
}

# Create service account with minimal required permissions
setup_service_account() {
    log "👤 Setting up service account..."
    
    SA_EMAIL="manga-service@${PROJECT_ID}.iam.gserviceaccount.com"
    
    if gcloud iam service-accounts describe "$SA_EMAIL" &>/dev/null; then
        info "✅ Service account already exists"
    else
        info "🔄 Creating service account..."
        gcloud iam service-accounts create manga-service \
            --display-name="AI Manga Service Account" \
            --description="Service account for AI Manga Generation Service"
    fi
    
    # Grant minimal required permissions
    info "🔄 Granting IAM permissions..."
    roles=(
        "roles/aiplatform.user"
        "roles/secretmanager.secretAccessor" 
        "roles/cloudsql.client"
        "roles/redis.viewer"
    )
    
    for role in "${roles[@]}"; do
        gcloud projects add-iam-policy-binding "$PROJECT_ID" \
            --member="serviceAccount:$SA_EMAIL" \
            --role="$role" \
            --quiet
    done
}

# Build and deploy using Cloud Build
deploy_service() {
    log "🚀 Starting production deployment..."
    
    # Check if cloudbuild-production.yaml exists
    if [[ ! -f "cloudbuild-production.yaml" ]]; then
        error "cloudbuild-production.yaml not found! Please ensure it exists."
    fi
    
    # Submit build
    info "🔄 Submitting Cloud Build job..."
    BUILD_ID=$(gcloud builds submit \
        --config=cloudbuild-production.yaml \
        --substitutions=_SERVICE_NAME="$SERVICE_NAME",_REGION="$REGION",_REPOSITORY="$REPOSITORY" \
        --format="value(id)")
    
    if [[ -z "$BUILD_ID" ]]; then
        error "Failed to submit build job"
    fi
    
    info "📋 Build ID: $BUILD_ID"
    info "🔗 Build logs: https://console.cloud.google.com/cloud-build/builds/$BUILD_ID?project=$PROJECT_ID"
    
    # Wait for build completion
    info "⏳ Waiting for build to complete..."
    gcloud builds wait "$BUILD_ID"
    
    BUILD_STATUS=$(gcloud builds describe "$BUILD_ID" --format="value(status)")
    if [[ "$BUILD_STATUS" != "SUCCESS" ]]; then
        error "Build failed with status: $BUILD_STATUS"
    fi
    
    info "✅ Build completed successfully"
}

# Post-deployment verification
verify_deployment() {
    log "🔍 Verifying deployment..."
    
    # Get service URL
    SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
        --region="$REGION" \
        --format='value(status.url)')
    
    if [[ -z "$SERVICE_URL" ]]; then
        error "Failed to get service URL"
    fi
    
    info "🔗 Service URL: $SERVICE_URL"
    
    # Health check with retries
    info "🔄 Running health checks..."
    for i in {1..10}; do
        if curl -f "$SERVICE_URL/health" --max-time 10 --silent; then
            info "✅ Health check passed"
            break
        fi
        if [[ $i -eq 10 ]]; then
            error "Health check failed after 10 attempts"
        fi
        info "⏳ Health check attempt $i/10 failed, retrying..."
        sleep 10
    done
    
    # Test API endpoints
    info "🔄 Testing API endpoints..."
    
    # Test info endpoint
    if curl -f "$SERVICE_URL/api/v1/info" --max-time 30 --silent; then
        info "✅ API info endpoint working"
    else
        warn "⚠️  API info endpoint test failed"
    fi
    
    # Test root endpoint
    if curl -f "$SERVICE_URL/" --max-time 30 --silent; then
        info "✅ Root endpoint working"
    else
        warn "⚠️  Root endpoint test failed"
    fi
}

# Display deployment summary
deployment_summary() {
    log "📊 Deployment Summary"
    
    SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
        --region="$REGION" \
        --format='value(status.url)')
    
    echo ""
    echo "🎉 Production deployment completed successfully!"
    echo ""
    echo "📋 Service Details:"
    echo "   • Service Name: $SERVICE_NAME"
    echo "   • Project: $PROJECT_ID"
    echo "   • Region: $REGION"
    echo "   • URL: $SERVICE_URL"
    echo ""
    echo "🔗 Important URLs:"
    echo "   • API Documentation: $SERVICE_URL/docs"
    echo "   • Health Check: $SERVICE_URL/health"
    echo "   • API Info: $SERVICE_URL/api/v1/info"
    echo "   • WebSocket: $SERVICE_URL/ws/v1/"
    echo ""
    echo "📊 Monitoring:"
    echo "   • Cloud Run Console: https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME?project=$PROJECT_ID"
    echo "   • Logs: gcloud run logs tail $SERVICE_NAME --region=$REGION"
    echo "   • Metrics: https://console.cloud.google.com/monitoring?project=$PROJECT_ID"
    echo ""
    echo "🔧 Next Steps:"
    echo "   1. Configure domain name and SSL certificate"
    echo "   2. Set up monitoring alerts"
    echo "   3. Configure CI/CD triggers"
    echo "   4. Update frontend CORS settings"
    echo "   5. Set up VPC connector for private networking"
    echo ""
}

# Cleanup function for error handling
cleanup() {
    if [[ $? -ne 0 ]]; then
        error "Deployment failed! Check the logs above for details."
    fi
}

# Set trap for cleanup
trap cleanup EXIT

# Main execution flow
main() {
    log "🚀 Starting AI Manga Generation Service Production Deployment"
    log "📋 Project: $PROJECT_ID | Region: $REGION | Service: $SERVICE_NAME"
    
    check_prerequisites
    enable_apis
    setup_artifact_registry
    setup_secrets
    setup_service_account
    deploy_service
    verify_deployment
    deployment_summary
    
    log "🎉 Deployment completed successfully!"
}

# Check if script is being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi