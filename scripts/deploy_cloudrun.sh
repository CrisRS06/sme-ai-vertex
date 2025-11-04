#!/bin/bash

###############################################################################
# Cloud Run Deployment Script for SME AI Vertex
#
# This script builds and deploys the FastAPI application to Cloud Run.
#
# Prerequisites:
# - gcloud CLI installed and authenticated
# - Docker installed (for local builds)
# - GCP project configured with billing enabled
# - APIs enabled (run scripts/setup_gcp.sh first)
#
# Usage:
#   ./scripts/deploy_cloudrun.sh <PROJECT_ID> <REGION> [SERVICE_NAME]
#
# Example:
#   ./scripts/deploy_cloudrun.sh my-sme-ai-project us-central1 sme-ai-vertex
###############################################################################

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check arguments
if [ $# -lt 2 ]; then
    print_error "Usage: $0 <PROJECT_ID> <REGION> [SERVICE_NAME]"
    exit 1
fi

PROJECT_ID=$1
REGION=$2
SERVICE_NAME=${3:-sme-ai-vertex}

# Set GCP project
gcloud config set project $PROJECT_ID
print_status "Project set to $PROJECT_ID"

###############################################################################
# Build and push container image
###############################################################################
print_status "Building container image..."

IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
IMAGE_TAG="latest"
FULL_IMAGE="${IMAGE_NAME}:${IMAGE_TAG}"

# Build using Cloud Build (recommended for Cloud Run)
gcloud builds submit --tag $FULL_IMAGE .

print_status "Container image built and pushed: $FULL_IMAGE"

###############################################################################
# Deploy to Cloud Run
###############################################################################
print_status "Deploying to Cloud Run..."

# Get service account email
SA_EMAIL="sme-ai-vertex-sa@${PROJECT_ID}.iam.gserviceaccount.com"

# Deploy
gcloud run deploy $SERVICE_NAME \
    --image $FULL_IMAGE \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --service-account $SA_EMAIL \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --concurrency 80 \
    --min-instances 0 \
    --max-instances 10 \
    --set-env-vars "GCP_PROJECT_ID=${PROJECT_ID}" \
    --set-env-vars "GCP_REGION=${REGION}" \
    --set-env-vars "ENVIRONMENT=production"

print_status "Deployment complete!"

###############################################################################
# Get service URL
###############################################################################
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --format 'value(status.url)')

echo ""
echo "========================================================================="
print_status "Cloud Run Deployment Successful!"
echo "========================================================================="
echo ""
echo "Service Name: $SERVICE_NAME"
echo "Region: $REGION"
echo "Service URL: $SERVICE_URL"
echo ""
echo "API Documentation: ${SERVICE_URL}/docs"
echo "Health Check: ${SERVICE_URL}/health"
echo ""
echo "Next steps:"
echo "  1. Test the API: curl ${SERVICE_URL}/health"
echo "  2. Upload knowledge base documents via /knowledgebase/upload"
echo "  3. Start analyzing drawings via /analysis/upload"
echo ""
print_warning "Note: Service is currently configured to allow unauthenticated access."
print_warning "For production, configure proper authentication (JWT, API Keys, etc.)"
echo "========================================================================="
