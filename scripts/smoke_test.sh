#!/bin/bash
# ============================================================================
# SME AI Vertex - Smoke Test Suite
# Quick health check for backend and frontend services (MVP mode)
# ============================================================================

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BACKEND_URL="${BACKEND_URL:-http://localhost:8080}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"
TIMEOUT=10

echo "🔬 SME AI Vertex - Smoke Test Suite"
echo "===================================="
echo ""

# Track results
TESTS_PASSED=0
TESTS_FAILED=0

# Test helper function
test_endpoint() {
    local name="$1"
    local url="$2"
    local expected_status="${3:-200}"

    echo -n "Testing $name... "

    if response=$(curl -s -o /dev/null -w "%{http_code}" --max-time $TIMEOUT "$url" 2>/dev/null); then
        if [ "$response" = "$expected_status" ]; then
            echo -e "${GREEN}✓ PASS${NC} (HTTP $response)"
            ((TESTS_PASSED++))
            return 0
        else
            echo -e "${RED}✗ FAIL${NC} (Expected HTTP $expected_status, got $response)"
            ((TESTS_FAILED++))
            return 1
        fi
    else
        echo -e "${RED}✗ FAIL${NC} (Connection failed)"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Test JSON response
test_json_endpoint() {
    local name="$1"
    local url="$2"
    local key="$3"

    echo -n "Testing $name... "

    if response=$(curl -s --max-time $TIMEOUT "$url" 2>/dev/null); then
        if echo "$response" | jq -e ".$key" > /dev/null 2>&1; then
            value=$(echo "$response" | jq -r ".$key")
            echo -e "${GREEN}✓ PASS${NC} ($key=$value)"
            ((TESTS_PASSED++))
            return 0
        else
            echo -e "${RED}✗ FAIL${NC} (Key '$key' not found in response)"
            ((TESTS_FAILED++))
            return 1
        fi
    else
        echo -e "${RED}✗ FAIL${NC} (Connection failed)"
        ((TESTS_FAILED++))
        return 1
    fi
}

echo "📡 Backend API Tests ($BACKEND_URL)"
echo "-----------------------------------"

# Test 1: Backend health endpoint
test_json_endpoint "Health Check" "$BACKEND_URL/health" "status"

# Test 2: Backend API root
test_endpoint "API Root" "$BACKEND_URL/"

# Test 3: OpenAPI docs
test_endpoint "OpenAPI Docs" "$BACKEND_URL/docs"

# Test 4: Knowledge base endpoint (should return empty array)
test_endpoint "Knowledge Base List" "$BACKEND_URL/knowledgebase/documents"

# Test 5: Analysis documents endpoint (should return empty array)
test_endpoint "Analysis List" "$BACKEND_URL/analysis/documents"

echo ""
echo "🌐 Frontend Tests ($FRONTEND_URL)"
echo "-----------------------------------"

# Test 6: Frontend homepage
test_endpoint "Homepage" "$FRONTEND_URL/"

# Test 7: Knowledge base page
test_endpoint "Knowledge Base Page" "$FRONTEND_URL/knowledge-base"

# Test 8: Analyze page
test_endpoint "Analyze Page" "$FRONTEND_URL/analyze"

# Test 9: Results page
test_endpoint "Results Page" "$FRONTEND_URL/results"

echo ""
echo "📊 Test Summary"
echo "==============="
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo -e "Total: $((TESTS_PASSED + TESTS_FAILED))"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All smoke tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some smoke tests failed${NC}"
    exit 1
fi
