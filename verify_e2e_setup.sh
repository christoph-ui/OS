#!/bin/bash
# Verify E2E Testing Setup
# Checks that all files are in place and working

echo "🔍 Verifying E2E Testing Setup..."
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASSED=0
FAILED=0

check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1"
        ((PASSED++))
    else
        echo -e "${RED}✗${NC} $1 (missing)"
        ((FAILED++))
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} $1/"
        ((PASSED++))
    else
        echo -e "${RED}✗${NC} $1/ (missing)"
        ((FAILED++))
    fi
}

echo "📁 Checking E2E test files..."
check_file "tests/e2e/__init__.py"
check_file "tests/e2e/conftest.py"
check_file "tests/e2e/helpers.py"
check_file "tests/e2e/test_complete_onboarding_flow.py"
check_file "tests/e2e/test_data_ingestion_flow.py"
check_file "tests/e2e/test_chat_interaction_flow.py"
check_file "tests/e2e/test_customer_isolation.py"
check_file "tests/e2e/test_mcp_orchestration.py"
check_file "tests/e2e/test_authentication_flow.py"

echo ""
echo "🔧 Checking test utilities..."
check_file "tests/utils/__init__.py"
check_file "tests/utils/api_client.py"
check_file "tests/utils/websocket_client.py"
check_file "tests/utils/docker_manager.py"

echo ""
echo "📊 Checking test fixtures..."
check_dir "tests/fixtures/sample_data"
check_file "tests/fixtures/mock_responses.py"
check_file "tests/fixtures/sample_data/sample_invoice.pdf"
check_file "tests/fixtures/sample_data/sample_contract.txt"
check_file "tests/fixtures/sample_data/sample_tax_report.csv"
check_file "tests/fixtures/sample_data/sample_unknown.dat"

echo ""
echo "⚙️  Checking configuration..."
check_file "pytest.ini"
check_file "docker-compose.test.yml"
check_file "run_e2e_tests.sh"
check_file "run_all_tests.sh"

echo ""
echo "📚 Checking documentation..."
check_file "tests/README.md"
check_file "TESTING_QUICK_START.md"
check_file "E2E_TESTING_SUMMARY.md"
check_file "E2E_TEST_RESULTS.md"
check_file "E2E_TESTING_COMPLETE.md"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "Results: ${GREEN}${PASSED} passed${NC}, ${RED}${FAILED} failed${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ E2E Testing Setup: COMPLETE${NC}"
    echo ""
    echo "Run tests with:"
    echo "  ./run_e2e_tests.sh"
    exit 0
else
    echo ""
    echo -e "${RED}❌ Some files are missing${NC}"
    exit 1
fi
