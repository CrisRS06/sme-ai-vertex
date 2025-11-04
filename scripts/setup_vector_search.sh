#!/usr/bin/env bash
#
# Setup script for Vertex AI Vector Search (Tree-AH) per Google Cloud Vertex AI RAG 2025 guide.
# Creates index + endpoint + deployment and outputs environment variables to append to .env.
#
# Usage:
#   ./scripts/setup_vector_search.sh PROJECT_ID REGION INDEX_DISPLAY_NAME
#
# Example:
#   ./scripts/setup_vector_search.sh my-gcp-project us-central1 sme-vector-index
#
set -euo pipefail

if [[ $# -lt 3 ]]; then
  echo "Usage: $0 PROJECT_ID REGION INDEX_DISPLAY_NAME [MACHINE_TYPE]" >&2
  exit 1
fi

PROJECT_ID="$1"
REGION="$2"
DISPLAY_NAME="$3"
MACHINE_TYPE="${4:-e2-standard-16}"

TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
INDEX_NAME="${DISPLAY_NAME}-${TIMESTAMP}"
ENDPOINT_NAME="${DISPLAY_NAME}-endpoint-${TIMESTAMP}"
DEPLOYED_INDEX_ID="${DISPLAY_NAME}-deployed"

echo "-> Enabling APIs (if not already enabled)..."
gcloud services enable aiplatform.googleapis.com --project "${PROJECT_ID}"

DELTA_BUCKET="gs://${PROJECT_ID}-vector-search-delta"

if ! gsutil ls "${DELTA_BUCKET}" >/dev/null 2>&1; then
  echo "-> Creating delta bucket ${DELTA_BUCKET}"
  gsutil mb -p "${PROJECT_ID}" -c STANDARD -l "${REGION}" "${DELTA_BUCKET}"
fi

echo "-> Creating Tree-AH index: ${INDEX_NAME}"
# Create temporary metadata file with required approximateNeighborsCount
METADATA_FILE=$(mktemp)
cat > "${METADATA_FILE}" <<EOF
{
  "contentsDeltaUri": "${DELTA_BUCKET}/${INDEX_NAME}",
  "config": {
    "algorithmConfig": {
      "treeAhConfig": {}
    },
    "approximateNeighborsCount": 1000,
    "dimensions": 1408,
    "distanceMeasureType": "COSINE_DISTANCE",
    "featureNormType": "UNIT_L2_NORM"
  }
}
EOF

INDEX_RESOURCE=$(gcloud alpha ai indexes create \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --display-name="${INDEX_NAME}" \
  --description="Tree-AH multimodal index for SME AI Vertex" \
  --metadata-file="${METADATA_FILE}")

# Clean up temporary file
rm -f "${METADATA_FILE}"

INDEX_ID=$(echo "${INDEX_RESOURCE}" | grep -o "projects/${PROJECT_ID}/locations/${REGION}/indexes/[0-9a-zA-Z\-]*")
echo "   Index resource: ${INDEX_ID}"

echo "-> Creating index endpoint: ${ENDPOINT_NAME}"
ENDPOINT_RESOURCE=$(gcloud alpha ai index-endpoints create \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --display-name="${ENDPOINT_NAME}")

ENDPOINT_ID=$(echo "${ENDPOINT_RESOURCE}" | grep -o "projects/${PROJECT_ID}/locations/${REGION}/indexEndpoints/[0-9a-zA-Z\-]*")
echo "   Endpoint resource: ${ENDPOINT_ID}"

echo "-> Deploying index to endpoint..."
gcloud alpha ai index-endpoints deploy-index "${ENDPOINT_ID}" \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --index="${INDEX_ID}" \
  --deployed-index-id="${DEPLOYED_INDEX_ID}" \
  --display-name="${DISPLAY_NAME}-deployment" \
  --machine-type="${MACHINE_TYPE}"

cat <<EOF

============================================================
Vector Search provisioning complete.
Add the following variables to your .env file:

VECTOR_SEARCH_INDEX_ID=${INDEX_ID}
VECTOR_SEARCH_ENDPOINT_ID=${ENDPOINT_ID}
VECTOR_SEARCH_DEPLOYED_INDEX_ID=${DEPLOYED_INDEX_ID}

NOTE:
- Update bucket ${PROJECT_ID}-vector-search-delta lifecycle/permissions as needed.
- Basic Tree-AH index created with approximateNeighborsCount=1000.
============================================================
EOF
