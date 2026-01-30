#!/bin/bash
# Start Cradle Services

set -e

echo "Starting Cradle Services..."
echo "=========================================="

cd /home/christoph.bertsch/0711/0711-cradle

# Check if network exists
if ! docker network ls | grep -q "cradle-network"; then
    echo "Creating cradle-network..."
    docker network create cradle-network
fi

# Start services
echo "Starting Cradle containers..."
docker-compose -f docker-compose.cradle.yml up -d

# Wait for services
echo "Waiting for services to start..."
sleep 10

# Health checks
echo ""
echo "Health Checks:"
echo "=========================================="

# Embedding service
echo -n "Embedding Service: "
if curl -s http://localhost:8001/health > /dev/null; then
    echo "✓ Healthy"
else
    echo "✗ Not responding"
fi

# Vision service
echo -n "Vision Service: "
if curl -s http://localhost:8002/health > /dev/null; then
    echo "✓ Healthy"
else
    echo "✗ Not responding"
fi

# Installation DB
echo -n "Installation DB: "
if PGPASSWORD=cradle_secret_2025 psql -h localhost -p 5433 -U cradle -d installation_configs -c "SELECT 1" > /dev/null 2>&1; then
    echo "✓ Healthy"
else
    echo "✗ Not responding"
fi

echo ""
echo "Cradle Services:"
docker-compose -f docker-compose.cradle.yml ps

echo ""
echo "=========================================="
echo "Cradle is ready!"
echo ""
echo "Services:"
echo "  - Embeddings: http://localhost:8001"
echo "  - Vision: http://localhost:8002"
echo "  - Installation DB: localhost:5433"
echo ""
