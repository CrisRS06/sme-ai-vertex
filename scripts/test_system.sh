#!/usr/bin/env bash
#
# Script de testing automatizado para SME AI Vertex
# Prueba todos los componentes principales del sistema
#
# Usage:
#   ./scripts/test_system.sh [API_URL]
#
# Examples:
#   ./scripts/test_system.sh http://localhost:8080
#   ./scripts/test_system.sh https://sme-ai-vertex-xxx-uc.a.run.app
#
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default API URL
API_URL="${1:-http://localhost:8080}"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  SME AI Vertex - Automated System Test"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Testing API at: $API_URL"
echo ""

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
test_passed() {
    echo -e "${GREEN}✓${NC} $1"
    ((TESTS_PASSED++))
}

test_failed() {
    echo -e "${RED}✗${NC} $1"
    ((TESTS_FAILED++))
}

test_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Test 1: Health Check
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 1: Health Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

HEALTH_RESPONSE=$(curl -s "$API_URL/health")
HEALTH_STATUS=$(echo "$HEALTH_RESPONSE" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)

if [ "$HEALTH_STATUS" = "healthy" ]; then
    test_passed "API is healthy"
else
    test_failed "API health check failed"
    echo "Response: $HEALTH_RESPONSE"
fi

# Check services
GCP_STATUS=$(echo "$HEALTH_RESPONSE" | grep -o '"gcp":"[^"]*"' | cut -d'"' -f4)
if [ "$GCP_STATUS" = "configured" ]; then
    test_passed "GCP configured"
else
    test_failed "GCP not configured"
fi

VERTEX_STATUS=$(echo "$HEALTH_RESPONSE" | grep -o '"vertex_ai":"[^"]*"' | cut -d'"' -f4)
if [ "$VERTEX_STATUS" = "enabled" ]; then
    test_passed "Vertex AI enabled"
else
    test_failed "Vertex AI not enabled"
fi

RAG_STATUS=$(echo "$HEALTH_RESPONSE" | grep -o '"rag_grounding":"[^"]*"' | cut -d'"' -f4)
if [ "$RAG_STATUS" = "configured" ]; then
    test_passed "RAG grounding configured"
elif [ "$RAG_STATUS" = "not_configured_warning" ]; then
    test_warning "RAG grounding not configured (optional for basic testing)"
else
    test_warning "RAG grounding status: $RAG_STATUS"
fi

echo ""

# Test 2: API Documentation
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 2: API Documentation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

DOCS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/docs")
if [ "$DOCS_RESPONSE" = "200" ]; then
    test_passed "Swagger UI accessible at $API_URL/docs"
else
    test_failed "Swagger UI not accessible (HTTP $DOCS_RESPONSE)"
fi

REDOC_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/redoc")
if [ "$REDOC_RESPONSE" = "200" ]; then
    test_passed "ReDoc accessible at $API_URL/redoc"
else
    test_failed "ReDoc not accessible (HTTP $REDOC_RESPONSE)"
fi

echo ""

# Test 3: Knowledge Base Endpoints
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 3: Knowledge Base Endpoints"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Test list documents
KB_LIST_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/knowledgebase/documents")
if [ "$KB_LIST_RESPONSE" = "200" ]; then
    test_passed "List documents endpoint working"
else
    test_failed "List documents endpoint failed (HTTP $KB_LIST_RESPONSE)"
fi

# Test stats
KB_STATS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/knowledgebase/stats")
if [ "$KB_STATS_RESPONSE" = "200" ]; then
    test_passed "Knowledge base stats endpoint working"
else
    test_failed "Knowledge base stats endpoint failed (HTTP $KB_STATS_RESPONSE)"
fi

echo ""

# Test 4: Analysis Endpoints
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 4: Analysis Endpoints"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Test list analyses
ANALYSIS_LIST_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/analysis/documents")
if [ "$ANALYSIS_LIST_RESPONSE" = "200" ]; then
    test_passed "List analyses endpoint working"
else
    test_failed "List analyses endpoint failed (HTTP $ANALYSIS_LIST_RESPONSE)"
fi

echo ""

# Test 5: Chat Endpoint (Basic)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 5: Chat Endpoint"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Test general chat
CHAT_RESPONSE=$(curl -s -X POST "$API_URL/analysis/general" \
    -H "Content-Type: application/json" \
    -d '{"message":"What is injection molding?","history":[]}')

CHAT_STATUS=$?
if [ $CHAT_STATUS -eq 0 ]; then
    # Check if response contains "message" field
    if echo "$CHAT_RESPONSE" | grep -q '"message"'; then
        test_passed "Chat endpoint working"

        # Check if grounded
        if echo "$CHAT_RESPONSE" | grep -q '"grounded":true'; then
            test_passed "Chat responses are grounded (RAG enabled)"
        else
            test_warning "Chat not grounded (RAG not configured - OK for basic testing)"
        fi
    else
        test_failed "Chat response invalid"
        echo "Response: $CHAT_RESPONSE"
    fi
else
    test_failed "Chat endpoint request failed"
fi

echo ""

# Test 6: Metrics Endpoint
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 6: Metrics Endpoint"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

METRICS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/metrics/summary")
if [ "$METRICS_RESPONSE" = "200" ]; then
    test_passed "Metrics endpoint working"
else
    test_warning "Metrics endpoint not accessible (HTTP $METRICS_RESPONSE) - OK if no data yet"
fi

echo ""

# Test 7: File Upload (If test files exist)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 7: File Upload (Optional)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if test files exist
if [ -f "test_manual.pdf" ]; then
    echo "Found test_manual.pdf, testing upload..."

    UPLOAD_RESPONSE=$(curl -s -X POST "$API_URL/knowledgebase/upload" \
        -F "file=@test_manual.pdf" \
        -F "document_type=manual")

    if echo "$UPLOAD_RESPONSE" | grep -q '"document_id"'; then
        test_passed "Document upload successful"
        DOCUMENT_ID=$(echo "$UPLOAD_RESPONSE" | grep -o '"document_id":"[^"]*"' | cut -d'"' -f4)
        echo "   Document ID: $DOCUMENT_ID"
    else
        test_failed "Document upload failed"
        echo "Response: $UPLOAD_RESPONSE"
    fi
else
    test_warning "No test_manual.pdf found - skipping upload test"
    echo "   Create test_manual.pdf to test uploads"
fi

if [ -f "test_drawing.pdf" ]; then
    echo "Found test_drawing.pdf, testing analysis..."

    ANALYSIS_RESPONSE=$(curl -s -X POST "$API_URL/analysis/upload" \
        -F "file=@test_drawing.pdf" \
        -F "project_name=SystemTest" \
        -F "quality_mode=flash")

    if echo "$ANALYSIS_RESPONSE" | grep -q '"analysis_id"'; then
        test_passed "Drawing analysis started"
        ANALYSIS_ID=$(echo "$ANALYSIS_RESPONSE" | grep -o '"analysis_id":"[^"]*"' | cut -d'"' -f4)
        echo "   Analysis ID: $ANALYSIS_ID"
        echo "   Status will be 'processing' initially"
        echo "   Check status at: $API_URL/analysis/$ANALYSIS_ID"
    else
        test_failed "Drawing analysis failed to start"
        echo "Response: $ANALYSIS_RESPONSE"
    fi
else
    test_warning "No test_drawing.pdf found - skipping analysis test"
    echo "   Create test_drawing.pdf to test analysis"
fi

echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Test Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}Tests Passed:${NC} $TESTS_PASSED"
echo -e "${RED}Tests Failed:${NC} $TESTS_FAILED"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All critical tests passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Open Swagger UI: $API_URL/docs"
    echo "  2. Try uploading a document"
    echo "  3. Try analyzing a drawing"
    echo "  4. Check out docs/TESTING_GUIDE.md for more"
    echo ""
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check .env configuration"
    echo "  2. Verify GCP credentials"
    echo "  3. Check logs for errors"
    echo "  4. See docs/TESTING_GUIDE.md"
    echo ""
    exit 1
fi
