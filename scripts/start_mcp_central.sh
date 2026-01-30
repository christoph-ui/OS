#!/bin/bash
# Start MCP Central Services

set -e

echo "Starting MCP Central Services..."
echo "=========================================="

cd /home/christoph.bertsch/0711/0711-mcp-central

# Check networks
if ! docker network ls | grep -q "mcp-central-network"; then
    echo "Creating mcp-central-network..."
    docker network create mcp-central-network
fi

if ! docker network ls | grep -q "platform-network"; then
    echo "Creating platform-network..."
    docker network create platform-network
fi

# Start services
echo "Starting MCP Central containers..."
docker-compose -f docker-compose.mcp-central.yml up -d

# Wait for services
echo "Waiting for services to start..."
sleep 10

# Health checks
echo ""
echo "Health Checks:"
echo "=========================================="

# MCP Central API
echo -n "MCP Central API: "
if curl -s http://localhost:4090/health > /dev/null; then
    echo "✓ Healthy"
    curl -s http://localhost:4090/ | jq '.'
else
    echo "✗ Not responding"
fi

# User Registry DB
echo -n "User Registry DB: "
if PGPASSWORD=mcp_central_secret psql -h localhost -p 5434 -U mcp_central -d user_registry -c "SELECT COUNT(*) FROM users" > /dev/null 2>&1; then
    USER_COUNT=$(PGPASSWORD=mcp_central_secret psql -h localhost -p 5434 -U mcp_central -d user_registry -t -c "SELECT COUNT(*) FROM users")
    echo "✓ Healthy ($USER_COUNT users)"
else
    echo "✗ Not responding"
fi

echo ""
echo "MCP Central Services:"
docker-compose -f docker-compose.mcp-central.yml ps

echo ""
echo "=========================================="
echo "MCP Central is ready!"
echo ""
echo "Services:"
echo "  - API: http://localhost:4090"
echo "  - User Registry: localhost:5434"
echo ""
echo "API Endpoints:"
echo "  - GET  http://localhost:4090/"
echo "  - GET  http://localhost:4090/health"
echo "  - POST http://localhost:4090/api/auth/login"
echo "  - POST http://localhost:4090/api/embeddings/generate"
echo "  - POST http://localhost:4090/api/vision/process"
echo ""
