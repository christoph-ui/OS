#!/bin/bash
# Run All Tests (Unit + Integration + E2E)
#
# This script runs the complete test suite with coverage reporting.

set -e

cd "$(dirname "$0")"

echo "🧪 0711 Intelligence Platform - Complete Test Suite"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Parse arguments
COVERAGE=true
MARKERS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --no-coverage)
            COVERAGE=false
            shift
            ;;
        --unit)
            MARKERS="unit"
            shift
            ;;
        --integration)
            MARKERS="integration"
            shift
            ;;
        --e2e)
            MARKERS="e2e"
            shift
            ;;
        --fast)
            MARKERS="not slow"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--no-coverage] [--unit|--integration|--e2e|--fast]"
            exit 1
            ;;
    esac
done

# Build pytest command
PYTEST_CMD="pytest -v"

if [ "$COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=ingestion --cov=lakehouse --cov=mcps --cov=orchestrator --cov=console --cov=api --cov-report=html --cov-report=term-missing"
fi

if [ -n "$MARKERS" ]; then
    PYTEST_CMD="$PYTEST_CMD -m \"$MARKERS\""
fi

# Run tests
echo -e "${BLUE}Running tests...${NC}"
echo "Command: $PYTEST_CMD"
echo ""

eval $PYTEST_CMD

TEST_EXIT_CODE=$?

echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"

    if [ "$COVERAGE" = true ]; then
        echo ""
        echo -e "${BLUE}Coverage report generated:${NC}"
        echo "  HTML: htmlcov/index.html"
        echo ""
        echo "Open with: firefox htmlcov/index.html"
    fi
else
    echo -e "${RED}✗ Some tests failed (exit code: $TEST_EXIT_CODE)${NC}"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"

exit $TEST_EXIT_CODE
