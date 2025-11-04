#!/bin/bash

###############################################################################
# GCP Setup Script for SME AI Vertex
#
# This script sets up the Google Cloud Platform environment including:
# - Enabling required APIs
# - Creating Cloud Storage buckets
# - Setting up service account with proper permissions
# - Creating RAG Engine corpus
#
# Prerequisites:
# - gcloud CLI installed and authenticated
# - Billing enabled on your GCP project
# - Appropriate permissions (Project Editor or Owner)
#
# Usage:
#   ./scripts/setup_gcp.sh <PROJECT_ID> <REGION>
#
# Example:
#   ./scripts/setup_gcp.sh my-sme-ai-project us-central1
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
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
    print_error "Usage: $0 <PROJECT_ID> <REGION>"
    print_error "Example: $0 my-sme-ai-project us-central1"
    exit 1
fi

PROJECT_ID=$1
REGION=$2
LOCATION=$REGION

print_status "Starting GCP setup for project: $PROJECT_ID in region: $REGION"

# Set the project
gcloud config set project $PROJECT_ID
print_status "Project set to $PROJECT_ID"

###############################################################################
# Enable APIs
###############################################################################
print_status "Enabling required Google Cloud APIs..."

apis=(
    "aiplatform.googleapis.com"           # Vertex AI
    "storage.googleapis.com"              # Cloud Storage
    "documentai.googleapis.com"           # Document AI
    "run.googleapis.com"                  # Cloud Run
    "cloudbuild.googleapis.com"           # Cloud Build
    "artifactregistry.googleapis.com"     # Artifact Registry
)

for api in "${apis[@]}"; do
    print_status "Enabling $api..."
    gcloud services enable $api --project=$PROJECT_ID
done

print_status "All APIs enabled successfully"

###############################################################################
# Create Cloud Storage Buckets
###############################################################################
print_status "Creating Cloud Storage buckets..."

BUCKET_MANUALS="${PROJECT_ID}-manuals"
BUCKET_DRAWINGS="${PROJECT_ID}-drawings"
BUCKET_REPORTS="${PROJECT_ID}-reports"

create_bucket() {
    local bucket_name=$1
    if gsutil ls -b gs://$bucket_name 2>/dev/null; then
        print_warning "Bucket gs://$bucket_name already exists"
    else
        gsutil mb -l $REGION -c STANDARD gs://$bucket_name
        print_status "Created bucket: gs://$bucket_name"
    fi
}

create_bucket $BUCKET_MANUALS
create_bucket $BUCKET_DRAWINGS
create_bucket $BUCKET_REPORTS

###############################################################################
# Create Service Account
###############################################################################
print_status "Creating service account..."

SA_NAME="sme-ai-vertex-sa"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

if gcloud iam service-accounts describe $SA_EMAIL --project=$PROJECT_ID 2>/dev/null; then
    print_warning "Service account $SA_EMAIL already exists"
else
    gcloud iam service-accounts create $SA_NAME \
        --display-name="SME AI Vertex Service Account" \
        --project=$PROJECT_ID
    print_status "Created service account: $SA_EMAIL"
fi

###############################################################################
# Grant IAM Roles to Service Account
###############################################################################
print_status "Granting IAM roles to service account..."

roles=(
    "roles/aiplatform.user"              # Vertex AI access
    "roles/storage.objectAdmin"          # Cloud Storage full access
    "roles/documentai.apiUser"           # Document AI access
)

for role in "${roles[@]}"; do
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SA_EMAIL" \
        --role="$role" \
        --quiet
    print_status "Granted $role to $SA_EMAIL"
done

###############################################################################
# Create Service Account Key
###############################################################################
print_status "Creating service account key..."

KEY_FILE="service-account-key.json"

if [ -f "$KEY_FILE" ]; then
    print_warning "Service account key file already exists: $KEY_FILE"
    read -p "Do you want to create a new key? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        gcloud iam service-accounts keys create $KEY_FILE \
            --iam-account=$SA_EMAIL \
            --project=$PROJECT_ID
        print_status "Created new service account key: $KEY_FILE"
    fi
else
    gcloud iam service-accounts keys create $KEY_FILE \
        --iam-account=$SA_EMAIL \
        --project=$PROJECT_ID
    print_status "Created service account key: $KEY_FILE"
fi

###############################################################################
# Create .env file
###############################################################################
print_status "Creating .env file..."

if [ -f ".env" ]; then
    print_warning ".env file already exists, creating .env.new instead"
    ENV_FILE=".env.new"
else
    ENV_FILE=".env"
fi

cat > $ENV_FILE << EOF
# Google Cloud Platform
GCP_PROJECT_ID=$PROJECT_ID
GCP_REGION=$REGION
GCP_LOCATION=$LOCATION
GOOGLE_APPLICATION_CREDENTIALS=./service-account-key.json

# Cloud Storage Buckets
GCS_BUCKET_MANUALS=$BUCKET_MANUALS
GCS_BUCKET_DRAWINGS=$BUCKET_DRAWINGS
GCS_BUCKET_REPORTS=$BUCKET_REPORTS

# Vertex AI Models
VERTEX_AI_MODEL_FLASH=gemini-2.5-flash
VERTEX_AI_MODEL_PRO=gemini-2.5-pro
VERTEX_AI_EMBEDDING_MODEL=multimodalembedding@001

# RAG Engine
RAG_CORPUS_NAME=molding-knowledge-base
VECTOR_SEARCH_INDEX_ID=
VECTOR_SEARCH_ENDPOINT_ID=

# Document AI (update after creating processor)
DOCUMENTAI_PROCESSOR_ID=

# API Configuration (CHANGE THESE IN PRODUCTION!)
API_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# Application Settings
ENVIRONMENT=development
DEBUG=True
LOG_LEVEL=INFO
MAX_UPLOAD_SIZE_MB=50

# Feature Flags
QUALITY_MODE=flash
ENABLE_DOCUMENT_AI_FALLBACK=true
ENABLE_CHAT=true

# Rate Limiting
RATE_LIMIT_PER_MINUTE=10

# Report Generation
REPORT_TEMPLATE_DIR=./templates
REPORT_OUTPUT_FORMAT=pdf
EOF

print_status "Created $ENV_FILE with your GCP configuration"

###############################################################################
# Summary
###############################################################################
echo ""
echo "========================================================================="
print_status "GCP Setup Complete!"
echo "========================================================================="
echo ""
echo "Resources created:"
echo "  ✓ APIs enabled (Vertex AI, Storage, Document AI, Cloud Run)"
echo "  ✓ Cloud Storage buckets:"
echo "      - gs://$BUCKET_MANUALS"
echo "      - gs://$BUCKET_DRAWINGS"
echo "      - gs://$BUCKET_REPORTS"
echo "  ✓ Service account: $SA_EMAIL"
echo "  ✓ Service account key: $KEY_FILE"
echo "  ✓ Environment file: $ENV_FILE"
echo ""
echo "Next steps:"
echo "  1. Review and update $ENV_FILE with any additional settings"
echo "  2. (Optional) Create Document AI processor for OCR fallback"
echo "  3. (Optional) Set up Vector Search index and endpoint"
echo "  4. Install Python dependencies: pip install -r requirements.txt"
echo "  5. Run the application: python main.py"
echo ""
print_warning "IMPORTANT: Keep service-account-key.json secure and never commit it to git!"
echo "========================================================================="
