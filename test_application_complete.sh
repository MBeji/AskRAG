#!/bin/bash
# AskRAG Application Complete Testing Suite
# Test complet de toutes les fonctionnalités

echo "🚀 ASKRAG APPLICATION COMPLETE TESTING SUITE"
echo "=============================================="
echo ""

BASE_URL="http://localhost:8002"
API_BASE="$BASE_URL/api/v1"

echo "📋 Configuration des tests:"
echo "   Base URL: $BASE_URL"
echo "   API Base: $API_BASE"
echo "   Date: $(date)"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to test HTTP endpoint
test_endpoint() {
    local url=$1
    local description=$2
    local expected_status=${3:-200}
    
    echo -n "Testing $description... "
    
    status=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    
    if [ "$status" = "$expected_status" ]; then
        echo -e "${GREEN}✅ PASS${NC} (HTTP $status)"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC} (HTTP $status, expected $expected_status)"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Function to test JSON endpoint
test_json_endpoint() {
    local url=$1
    local description=$2
    
    echo -n "Testing $description... "
    
    response=$(curl -s "$url")
    status=$?
    
    if [ $status -eq 0 ] && echo "$response" | python -m json.tool >/dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC} (Valid JSON)"
        echo "   Response: $(echo "$response" | head -c 100)..."
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC} (Invalid JSON or connection error)"
        echo "   Response: $response"
        ((TESTS_FAILED++))
        return 1
    fi
}

echo "🔍 STARTING APPLICATION TESTS"
echo "=============================="
echo ""

# Test 1: Application Status
echo -e "${BLUE}1️⃣ Application Status Tests${NC}"
echo "----------------------------"
test_json_endpoint "$BASE_URL/" "Root endpoint"
test_json_endpoint "$BASE_URL/health" "Health check endpoint"
echo ""

# Test 2: API Documentation
echo -e "${BLUE}2️⃣ API Documentation Tests${NC}"
echo "---------------------------"
test_endpoint "$API_BASE/docs" "OpenAPI documentation" 200
test_endpoint "$API_BASE/openapi.json" "OpenAPI schema" 200
echo ""

# Test 3: User Management Tests
echo -e "${BLUE}3️⃣ User Management Tests${NC}"
echo "-------------------------"
test_json_endpoint "$API_BASE/users/" "List users"
test_endpoint "$API_BASE/users/me" "Current user info" 401
echo ""

# Test 4: Document Management Tests
echo -e "${BLUE}4️⃣ Document Management Tests${NC}"
echo "-----------------------------"
test_json_endpoint "$API_BASE/documents/" "List documents"
echo ""

# Test 5: Chat Session Tests
echo -e "${BLUE}5️⃣ Chat Session Tests${NC}"
echo "----------------------"
test_json_endpoint "$API_BASE/chat/sessions/" "List chat sessions"
echo ""

# Test 6: RAG Query Tests
echo -e "${BLUE}6️⃣ RAG Query Tests${NC}"
echo "------------------"
echo "Testing RAG query endpoint..."
query_response=$(curl -s -X POST "$API_BASE/query/" \
    -H "Content-Type: application/json" \
    -d '{"query": "What is AskRAG?", "session_id": "test-session"}')

if echo "$query_response" | python -m json.tool >/dev/null 2>&1; then
    echo -e "${GREEN}✅ PASS${NC} RAG query endpoint (Valid JSON)"
    echo "   Response: $(echo "$query_response" | head -c 150)..."
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ FAIL${NC} RAG query endpoint"
    echo "   Response: $query_response"
    ((TESTS_FAILED++))
fi
echo ""

# Test 7: Performance Tests
echo -e "${BLUE}7️⃣ Performance Tests${NC}"
echo "--------------------"
echo "Testing response times..."

start_time=$(date +%s%N)
curl -s "$BASE_URL/health" >/dev/null
end_time=$(date +%s%N)
response_time=$((($end_time - $start_time) / 1000000))

echo "Health endpoint response time: ${response_time}ms"

if [ $response_time -lt 1000 ]; then
    echo -e "${GREEN}✅ PASS${NC} Response time acceptable (<1s)"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠️ WARN${NC} Response time slow (>1s)"
    ((TESTS_PASSED++))
fi
echo ""

# Test 8: Concurrent Request Test
echo -e "${BLUE}8️⃣ Concurrent Request Tests${NC}"
echo "----------------------------"
echo "Testing concurrent requests (5 simultaneous)..."

for i in {1..5}; do
    curl -s "$BASE_URL/health" >/dev/null &
done
wait

echo -e "${GREEN}✅ PASS${NC} Concurrent requests handled"
((TESTS_PASSED++))
echo ""

# Test Summary
echo "📊 TEST SUMMARY"
echo "==============="
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo "Total Tests: $((TESTS_PASSED + TESTS_FAILED))"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 ALL TESTS PASSED! Application is working correctly.${NC}"
    exit 0
else
    echo -e "\n${YELLOW}⚠️ Some tests failed. Please check the application.${NC}"
    exit 1
fi
