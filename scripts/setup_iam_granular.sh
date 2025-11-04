#!/bin/bash
#
# Setup IAM Granular para Vertex AI RAG Engine
# Configura roles específicos y Service Accounts según mejores prácticas
#

set -e

PROJECT_ID=${1:-""}

if [ -z "$PROJECT_ID" ]; then
    echo "Error: PROJECT_ID is required"
    echo "Usage: ./setup_iam_granular.sh PROJECT_ID"
    echo "Example: ./setup_iam_granular.sh sustained-truck-408014"
    exit 1
fi

echo "=========================================="
echo "Configuring Granular IAM for RAG Engine"
echo "Project: $PROJECT_ID"
echo "=========================================="

# Enable required APIs
echo "Enabling required APIs..."
gcloud services enable \
    iam.googleapis.com \
    cloudresourcemanager.googleapis.com \
    aiplatform.googleapis.com \
    documentai.googleapis.com \
    --project=$PROJECT_ID

echo "✓ APIs enabled"

# Step 1: Create custom role for RAG Application Admin
echo ""
echo "Step 1: Creating custom role VertexRagAppAdmin..."
gcloud iam roles create VertexRagAppAdmin --project=${PROJECT_ID} \
    --title="Vertex AI RAG Application Admin" \
    --description="Permits create, manage and query RAG Engine corpora and use Gemini" \
    --permissions="aiplatform.ragCorpora.create,aiplatform.ragCorpora.get,aiplatform.ragCorpora.list,aiplatform.ragCorpora.delete,aiplatform.ragFiles.import,aiplatform.ragFiles.get,aiplatform.ragFiles.list,aiplatform.ragFiles.delete,aiplatform.ragCorpora.query,aiplatform.endpoints.predict,aiplatform.endpoints.list,aiplatform.endpoints.get" \
    --stage=GA

echo "✓ Custom role created"

# Step 2: Create Service Account for Application
echo ""
echo "Step 2: Creating Service Account rag-app-sa..."
gcloud iam service-accounts create rag-app-sa \
    --display-name="Service Account for RAG FastAPI Application" \
    --description="SA for RAG application to manage corpora and call Gemini" \
    --project=${PROJECT_ID}

echo "✓ Service Account rag-app-sa created"

# Step 3: Assign custom role to Service Account
echo ""
echo "Step 3: Assigning VertexRagAppAdmin role..."
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:rag-app-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="projects/${PROJECT_ID}/roles/VertexRagAppAdmin"

echo "✓ Custom role assigned"

# Step 4: Assign Storage permissions to Service Account
echo ""
echo "Step 4: Assigning Storage permissions..."
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:rag-app-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:rag-app-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

echo "✓ Storage permissions assigned"

# Step 5: Get Project Number and configure RAG Service Agent
echo ""
echo "Step 5: Configuring RAG Service Agent..."

PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} --format="value(projectNumber)")
RAG_SERVICE_AGENT="service-${PROJECT_NUMBER}@gcp-sa-vertex-rag.iam.gserviceaccount.com"

echo "  Project Number: $PROJECT_NUMBER"
echo "  RAG Service Agent: $RAG_SERVICE_AGENT"

# Step 6: Give Storage Viewer permission to RAG Service Agent
echo ""
echo "Step 6: Assigning Storage permissions to RAG Service Agent..."

# Function to add permissions to a bucket
configure_bucket_permissions() {
    local bucket_name=$1
    echo "  Configuring bucket: $bucket_name"
    
    # Check if bucket exists
    if gcloud storage buckets describe gs://$bucket_name --project=$PROJECT_ID &>/dev/null; then
        gcloud storage buckets add-iam-policy-binding gs://$bucket_name \
            --member="serviceAccount:${RAG_SERVICE_AGENT}" \
            --role="roles/storage.objectViewer"
        
        echo "    ✓ Storage.viewer assigned for $bucket_name"
    else
        echo "    ⚠ Bucket $bucket_name does not exist yet"
    fi
}

# Configure known buckets
configure_bucket_permissions "sme-ai-manuals"
configure_bucket_permissions "sme-ai-drawings"
configure_bucket_permissions "sme-ai-reports"

# Step 7: Give Document AI permission to RAG Service Agent
echo ""
echo "Step 7: Assigning Document AI permissions to RAG Service Agent..."
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${RAG_SERVICE_AGENT}" \
    --role="roles/documentai.apiUser"

echo "✓ Document AI permissions assigned"

# Step 8: Generate key for local development (optional)
echo ""
echo "Step 8: Generating service account key for local development..."
read -p "Do you want to generate a service account key for local development? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    gcloud iam service-accounts keys create service-account-key.json \
        --iam-account=rag-app-sa@${PROJECT_ID}.iam.gserviceaccount.com \
        --project=${PROJECT_ID}
    
    echo "✓ Service account key generated: service-account-key.json"
    echo "⚠ IMPORTANT: Store this key securely and never commit to version control"
fi

echo ""
echo "=========================================="
echo "✓ IAM Granular Setup Complete!"
echo "=========================================="
echo ""
echo "Service Account Details:"
echo "  Name: rag-app-sa@${PROJECT_ID}.iam.gserviceaccount.com"
echo "  Custom Role: projects/${PROJECT_ID}/roles/VertexRagAppAdmin"
echo "  Storage Role: roles/storage.objectAdmin"
echo ""
echo "RAG Service Agent:"
echo "  Name: ${RAG_SERVICE_AGENT}"
echo "  Storage Role: roles/storage.objectViewer"
echo "  Document AI Role: roles/documentai.apiUser"
echo ""
echo "Add these to your .env file:"
echo "GOOGLE_APPLICATION_CREDENTIALS=./service-account-key.json"
echo "RAG_SERVICE_ACCOUNT=rag-app-sa@${PROJECT_ID}.iam.gserviceaccount.com"
echo "RAG_SERVICE_AGENT=${RAG_SERVICE_AGENT}"
echo ""
echo "For Cloud Run deployment:"
echo "gcloud run deploy rag-fastapi-service \\"
echo "  --service-account=rag-app-sa@${PROJECT_ID}.iam.gserviceaccount.com"
echo ""
echo "=========================================="
