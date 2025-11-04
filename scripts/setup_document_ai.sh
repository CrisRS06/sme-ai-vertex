#!/bin/bash
#
# Setup Document AI OCR Processor for micr text fallback
# This is REQUIRED for production use - ensures no information is lost
#

set -e

PROJECT_ID=${1:-""}
LOCATION="us"  # Document AI processors must be in 'us' or 'eu'

if [ -z "$PROJECT_ID" ]; then
    echo "Error: PROJECT_ID is required"
    echo "Usage: ./setup_document_ai.sh PROJECT_ID"
    echo "Example: ./setup_document_ai.sh sustained-truck-408014"
    exit 1
fi

echo "=========================================="
echo "Setting up Document AI OCR Processor"
echo "Project: $PROJECT_ID"
echo "Location: $LOCATION (fixed for Document AI)"
echo "=========================================="

# Enable required APIs
echo "Enabling Document AI API..."
gcloud services enable \
    documentai.googleapis.com \
    --project=$PROJECT_ID

echo "✓ API enabled"

# Wait for API to propagate
echo "Waiting for API to be ready..."
sleep 5

# Create OCR Processor
echo ""
echo "Creating Document AI OCR Processor..."
echo "Processor Type: FORM_PARSER_PROCESSOR (best for technical drawings)"

PROCESSOR_DISPLAY_NAME="Drawing OCR Fallback"

# Check if processor already exists
echo "Checking if processor exists..."
EXISTING=$(gcloud alpha document-ai processors list \
    --location=$LOCATION \
    --project=$PROJECT_ID \
    --format="value(name)" \
    --filter="displayName:'$PROCESSOR_DISPLAY_NAME'" 2>/dev/null || echo "")

if [ -n "$EXISTING" ]; then
    echo "✓ Processor already exists: $EXISTING"
    PROCESSOR_ID=$(echo $EXISTING | awk -F'/' '{print $NF}')
else
    echo "Creating new processor..."

    # Create processor
    CREATE_OUTPUT=$(gcloud alpha document-ai processors create \
        --location=$LOCATION \
        --project=$PROJECT_ID \
        --display-name="$PROCESSOR_DISPLAY_NAME" \
        --type=FORM_PARSER_PROCESSOR \
        --format="value(name)")

    if [ -n "$CREATE_OUTPUT" ]; then
        PROCESSOR_ID=$(echo $CREATE_OUTPUT | awk -F'/' '{print $NF}')
        echo "✓ Processor created successfully"
    else
        echo "✗ Failed to create processor"
        echo ""
        echo "Manual creation instructions:"
        echo "1. Go to: https://console.cloud.google.com/ai/document-ai/processors"
        echo "2. Click 'Create Processor'"
        echo "3. Select 'Form Parser'"
        echo "4. Name: '$PROCESSOR_DISPLAY_NAME'"
        echo "5. Region: US"
        echo "6. Click 'Create'"
        echo "7. Copy the Processor ID from the URL"
        exit 1
    fi
fi

# Full processor name
PROCESSOR_NAME="projects/$PROJECT_ID/locations/$LOCATION/processors/$PROCESSOR_ID"

echo ""
echo "=========================================="
echo "✓ Document AI Setup Complete!"
echo "=========================================="
echo ""
echo "Processor ID:"
echo "$PROCESSOR_ID"
echo ""
echo "Full Processor Name:"
echo "$PROCESSOR_NAME"
echo ""
echo "Add this to your .env file:"
echo "DOCUMENT_AI_PROCESSOR_ID=$PROCESSOR_ID"
echo "ENABLE_DOCUMENT_AI_FALLBACK=true"
echo "OCR_CONFIDENCE_THRESHOLD=0.7"
echo ""
echo "=========================================="
echo "How it works:"
echo "=========================================="
echo ""
echo "1. VLM analyzes drawing with Gemini 2.5"
echo "2. If dimension confidence < 0.7:"
echo "   → Automatically triggers Document AI OCR"
echo "   → Extracts microtext with high precision"
echo "   → Merges results with VLM output"
echo "   → Tracks metrics (fields recovered, confidence)"
echo ""
echo "3. Result: No information lost! ✅"
echo ""
echo "Cost: ~\$0.0015 per page when triggered"
echo "Typical usage: 10-20% of pages need fallback"
echo ""
echo "=========================================="
