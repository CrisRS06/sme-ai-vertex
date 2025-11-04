#!/bin/bash
#
# Setup RAG Engine (Vertex AI Search) for Knowledge Base Grounding
# This is REQUIRED for production use
#

set -e

PROJECT_ID=${1:-""}
LOCATION=${2:-"us-central1"}

if [ -z "$PROJECT_ID" ]; then
    echo "Error: PROJECT_ID is required"
    echo "Usage: ./setup_rag_engine.sh PROJECT_ID [LOCATION]"
    echo "Example: ./setup_rag_engine.sh sustained-truck-408014 us-central1"
    exit 1
fi

echo "=========================================="
echo "Setting up RAG Engine (Vertex AI Search)"
echo "Project: $PROJECT_ID"
echo "Location: $LOCATION"
echo "=========================================="

# Enable required APIs
echo "Enabling Vertex AI Search API..."
gcloud services enable \
    discoveryengine.googleapis.com \
    --project=$PROJECT_ID

echo "✓ API enabled"

# Create Data Store
echo ""
echo "Creating RAG Data Store for manuals..."
echo "NOTE: This creates an unstructured data store for PDF manuals"

DATA_STORE_ID="manuals-knowledge-base"
DATA_STORE_NAME="Molding Manuals Knowledge Base"

# Check if data store already exists
echo "Checking if data store exists..."
EXISTING=$(gcloud alpha discovery-engine data-stores list \
    --location=$LOCATION \
    --project=$PROJECT_ID \
    --format="value(name)" \
    --filter="displayName:'$DATA_STORE_NAME'" 2>/dev/null || echo "")

if [ -n "$EXISTING" ]; then
    echo "✓ Data store already exists: $EXISTING"
    RAG_RESOURCE=$(echo $EXISTING | sed 's|.*/dataStores/||')
else
    echo "Creating new data store..."

    # Create data store
    gcloud alpha discovery-engine data-stores create $DATA_STORE_ID \
        --location=$LOCATION \
        --project=$PROJECT_ID \
        --collection=default_collection \
        --display-name="$DATA_STORE_NAME" \
        --industry-vertical=GENERIC \
        --content-config=CONTENT_REQUIRED \
        --solution-type=SOLUTION_TYPE_SEARCH

    echo "✓ Data store created: $DATA_STORE_ID"
    RAG_RESOURCE=$DATA_STORE_ID
fi

# Full resource name
RAG_CORPUS="projects/$PROJECT_ID/locations/$LOCATION/collections/default_collection/dataStores/$RAG_RESOURCE"

echo ""
echo "=========================================="
echo "✓ RAG Engine Setup Complete!"
echo "=========================================="
echo ""
echo "RAG Corpus Resource Name:"
echo "$RAG_CORPUS"
echo ""
echo "Add this to your .env file:"
echo "RAG_DATA_STORE_ID=$RAG_CORPUS"
echo "ENABLE_GROUNDING=true"
echo ""
echo "=========================================="
echo "Next Steps:"
echo "=========================================="
echo ""
echo "1. Add RAG_DATA_STORE_ID to .env"
echo "2. Upload manuals to the data store:"
echo ""
echo "   # Option A: Via Console (Recommended for first time)"
echo "   # https://console.cloud.google.com/gen-app-builder/engines"
echo ""
echo "   # Option B: Via gcloud"
echo "   gcloud alpha discovery-engine documents import \\"
echo "     --data-store=$DATA_STORE_ID \\"
echo "     --location=$LOCATION \\"
echo "     --project=$PROJECT_ID \\"
echo "     --gcs-uri=gs://YOUR_BUCKET/manuals/*.pdf"
echo ""
echo "3. Wait 5-10 minutes for indexing"
echo "4. Test with chat endpoint"
echo ""
echo "=========================================="
