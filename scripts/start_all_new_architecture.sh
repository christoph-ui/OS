#!/bin/bash
# Start Complete 0711 Platform with New Architecture
#
# Order:
# 1. Infrastructure (Postgres, Redis, MinIO)
# 2. Cradle (GPU Services)
# 3. MCP Central
# 4. Platform API
# 5. Customer Deployments (EATON, Lightnet)

set -e

echo "=========================================="
echo "Starting 0711 Platform (New Architecture)"
echo "=========================================="
echo ""

# Check if running from correct directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Step 1: Infrastructure
echo "Step 1: Starting Infrastructure..."
echo "  - PostgreSQL (Port 4005)"
echo "  - Redis (Port 6379)"
echo "  - MinIO (Port 4050/4051)"
echo ""

docker-compose up -d postgres redis minio

echo "  Waiting for infrastructure (10 seconds)..."
sleep 10

# Check infrastructure
if PGPASSWORD=0711_secret psql -h localhost -p 4005 -U 0711_user -d 0711_db -c "SELECT 1" > /dev/null 2>&1; then
    echo "✓ PostgreSQL ready"
else
    echo "✗ PostgreSQL not ready"
fi

if redis-cli -p 6379 ping > /dev/null 2>&1; then
    echo "✓ Redis ready"
else
    echo "✗ Redis not ready"
fi

if curl -s http://localhost:4050/minio/health/live > /dev/null 2>&1; then
    echo "✓ MinIO ready"
else
    echo "✗ MinIO not ready"
fi

echo ""

# Step 2: Cradle
echo "Step 2: Starting Cradle (GPU Services)..."
./scripts/start_cradle.sh

echo ""

# Step 3: MCP Central
echo "Step 3: Starting MCP Central..."
./scripts/start_mcp_central.sh

echo ""

# Step 4: Platform API
echo "Step 4: Starting Platform API (Port 4080)..."

# Check if already running
if curl -s http://localhost:4080/health > /dev/null 2>&1; then
    echo "  Platform API already running"
else
    cd /home/christoph.bertsch/0711/0711-OS

    # Start in background
    nohup python3 -m uvicorn api.main:app --host 0.0.0.0 --port 4080 > /tmp/platform-api.log 2>&1 &
    PLATFORM_PID=$!
    echo $PLATFORM_PID > /tmp/platform-api.pid

    echo "  Waiting for Platform API (10 seconds)..."
    sleep 10

    if curl -s http://localhost:4080/health > /dev/null; then
        echo "✓ Platform API ready (PID: $PLATFORM_PID)"
    else
        echo "✗ Platform API not ready (check /tmp/platform-api.log)"
    fi
fi

echo ""

# Step 5: Check Customer Deployments
echo "Step 5: Checking Customer Deployments..."

# EATON
if [ -d "/home/christoph.bertsch/0711/deployments/eaton" ]; then
    echo "  EATON deployment found"

    cd /home/christoph.bertsch/0711/deployments/eaton

    # Check if running
    if docker-compose ps | grep -q "Up"; then
        echo "  ✓ EATON containers running"
    else
        echo "  Starting EATON containers..."
        docker-compose up -d
        sleep 10
        echo "  ✓ EATON started"
    fi
else
    echo "  EATON deployment not found (run migration first)"
fi

# Lightnet
if [ -d "/home/christoph.bertsch/0711/deployments/lightnet" ]; then
    echo "  Lightnet deployment found"

    cd /home/christoph.bertsch/0711/deployments/lightnet

    # Check if running
    if docker-compose ps | grep -q "Up"; then
        echo "  ✓ Lightnet containers running"
    else
        echo "  Starting Lightnet containers..."
        docker-compose up -d
        sleep 10
        echo "  ✓ Lightnet started"
    fi
else
    echo "  Lightnet deployment not found (run migration first)"
fi

echo ""

# Summary
echo "=========================================="
echo "0711 Platform Started!"
echo "=========================================="
echo ""
echo "Infrastructure:"
echo "  - PostgreSQL: localhost:4005"
echo "  - Redis: localhost:6379"
echo "  - MinIO: http://localhost:4050"
echo ""
echo "Cradle (GPU Services):"
echo "  - Embeddings: http://localhost:8001"
echo "  - Vision: http://localhost:8002"
echo "  - Installation DB: localhost:5433"
echo ""
echo "MCP Central:"
echo "  - API: http://localhost:4090"
echo "  - User Registry: localhost:5434"
echo ""
echo "Platform:"
echo "  - API: http://localhost:4080"
echo ""
echo "Customers:"
echo "  - EATON Console: http://localhost:4020"
echo "  - EATON Lakehouse: http://localhost:9302"
echo "  - Lightnet Console: http://localhost:4021"
echo "  - Lightnet Lakehouse: http://localhost:9303"
echo ""
echo "Next Steps:"
echo "  1. Test services: curl http://localhost:4090/health"
echo "  2. Migrate EATON: ./scripts/migrate_eaton.sh"
echo "  3. Migrate Lightnet: ./scripts/migrate_lightnet.sh"
echo ""
