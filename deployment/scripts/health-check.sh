#!/bin/bash

#═══════════════════════════════════════════════════════════════════════════
# 0711 Platform Health Check
#
# Verifies that all services are running and healthy.
#═══════════════════════════════════════════════════════════════════════════

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
API_PORT=${API_PORT:-8080}
CONSOLE_PORT=${CONSOLE_PORT:-3000}
VLLM_PORT=${VLLM_PORT:-8001}
RAY_PORT=${RAY_DASHBOARD_PORT:-8265}
MINIO_PORT=${MINIO_PORT:-9000}

echo "🏥 0711 Platform Health Check"
echo "================================"
echo ""

# Function to check HTTP endpoint
check_http() {
    local name=$1
    local url=$2
    local timeout=${3:-5}

    if curl -sf --max-time $timeout "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name"
        return 0
    else
        echo -e "${RED}✗${NC} $name"
        return 1
    fi
}

# Check services
FAILED=0

# MinIO
if ! check_http "MinIO Object Storage" "http://localhost:${MINIO_PORT}/minio/health/live"; then
    ((FAILED++))
fi

# vLLM
if ! check_http "vLLM Inference Server" "http://localhost:${VLLM_PORT}/health" 30; then
    ((FAILED++))
fi

# Ray Dashboard
if ! check_http "Ray Cluster" "http://localhost:${RAY_PORT}"; then
    ((FAILED++))
fi

# Console Backend
if ! check_http "Console API" "http://localhost:${API_PORT}/health"; then
    ((FAILED++))
fi

# Console Frontend
if ! check_http "Console UI" "http://localhost:${CONSOLE_PORT}"; then
    ((FAILED++))
fi

echo ""
echo "================================"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All services healthy${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  $FAILED service(s) unhealthy${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  - Check logs: docker compose logs <service-name>"
    echo "  - View all containers: docker compose ps"
    echo "  - Restart services: docker compose restart"
    exit 1
fi
