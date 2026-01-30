#!/bin/bash
# Run End-to-End Tests
#
# This script starts the necessary services and runs E2E tests.

set -e

cd "$(dirname "$0")"

echo "🧪 0711 Intelligence Platform - E2E Test Runner"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if services are already running
check_service() {
    local service=$1
    local url=$2
    if curl -s -f "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ $service is running${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠ $service is not running${NC}"
        return 1
    fi
}

echo -e "${BLUE}Checking services...${NC}"
echo ""

services_running=true
if ! check_service "Control Plane API" "http://localhost:4080/health"; then
    services_running=false
fi
if ! check_service "Console Backend" "http://localhost:4010/health"; then
    services_running=false
fi

echo ""

if [ "$services_running" = false ]; then
    echo -e "${YELLOW}Some services are not running. Please start them first:${NC}"
    echo ""
    echo "  ./START_ALL.sh"
    echo ""
    echo "Or run in test mode:"
    echo "  docker-compose -f docker-compose.test.yml up -d"
    echo ""
    exit 1
fi

# Run tests
echo -e "${BLUE}Running E2E tests...${NC}"
echo ""

# Default: Run all E2E tests
TEST_MARKER="${1:-e2e}"

case "$TEST_MARKER" in
    "all")
        echo "Running ALL E2E tests..."
        pytest -v -m e2e tests/e2e/
        ;;
    "fast")
        echo "Running fast E2E tests (excluding slow tests)..."
        pytest -v -m "e2e and not slow" tests/e2e/
        ;;
    "onboarding")
        echo "Running onboarding flow tests..."
        pytest -v tests/e2e/test_complete_onboarding_flow.py
        ;;
    "ingestion")
        echo "Running data ingestion tests..."
        pytest -v tests/e2e/test_data_ingestion_flow.py
        ;;
    "chat")
        echo "Running chat interaction tests..."
        pytest -v tests/e2e/test_chat_interaction_flow.py
        ;;
    "isolation")
        echo "Running customer isolation tests..."
        pytest -v tests/e2e/test_customer_isolation.py
        ;;
    "mcp")
        echo "Running MCP orchestration tests..."
        pytest -v tests/e2e/test_mcp_orchestration.py
        ;;
    "auth")
        echo "Running authentication tests..."
        pytest -v tests/e2e/test_authentication_flow.py
        ;;
    *)
        echo "Running E2E tests with marker: $TEST_MARKER..."
        pytest -v -m "$TEST_MARKER" tests/e2e/
        ;;
esac

TEST_EXIT_CODE=$?

echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
else
    echo -e "${RED}✗ Some tests failed (exit code: $TEST_EXIT_CODE)${NC}"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"

exit $TEST_EXIT_CODE
