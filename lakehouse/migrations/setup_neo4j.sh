#!/bin/bash
# Setup Neo4j for 0711-OS Lakehouse
# Graph database for entity relationships

set -e

echo "=========================================="
echo "NEO4J SETUP FOR 0711-OS"
echo "=========================================="
echo ""

# Check if Neo4j container already exists
if docker ps -a | grep -q neo4j-0711; then
    echo "⚠️  Neo4j container already exists"
    read -p "Remove and recreate? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing existing container..."
        docker rm -f neo4j-0711 || true
    else
        echo "Using existing container"
        docker start neo4j-0711 2>/dev/null || true
        echo "✓ Neo4j container started"
        exit 0
    fi
fi

# Set password (default or custom)
NEO4J_PASSWORD="${NEO4J_PASSWORD:-zeroseven2024}"

echo "Starting Neo4j container..."
docker run -d \
  --name neo4j-0711 \
  --restart unless-stopped \
  -p 7474:7474 \
  -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/${NEO4J_PASSWORD} \
  -e NEO4J_PLUGINS='["apoc", "graph-data-science"]' \
  -e NEO4J_dbms_memory_heap_initial__size=512m \
  -e NEO4J_dbms_memory_heap_max__size=2g \
  -e NEO4J_dbms_memory_pagecache_size=1g \
  -v neo4j-0711-data:/data \
  -v neo4j-0711-logs:/logs \
  -v neo4j-0711-import:/var/lib/neo4j/import \
  -v neo4j-0711-plugins:/plugins \
  neo4j:5.15

echo ""
echo "Waiting for Neo4j to start..."
sleep 10

# Wait for Neo4j to be ready
MAX_WAIT=60
ELAPSED=0
while ! docker exec neo4j-0711 cypher-shell -u neo4j -p ${NEO4J_PASSWORD} "RETURN 1" > /dev/null 2>&1; do
    if [ $ELAPSED -ge $MAX_WAIT ]; then
        echo "✗ Neo4j failed to start within ${MAX_WAIT} seconds"
        echo "Check logs: docker logs neo4j-0711"
        exit 1
    fi
    echo -n "."
    sleep 2
    ELAPSED=$((ELAPSED + 2))
done

echo ""
echo ""
echo "=========================================="
echo "✓ NEO4J READY!"
echo "=========================================="
echo ""
echo "Connection Details:"
echo "  Browser:  http://localhost:7474"
echo "  Bolt URI: bolt://localhost:7687"
echo "  Username: neo4j"
echo "  Password: ${NEO4J_PASSWORD}"
echo ""
echo "Quick Commands:"
echo "  docker logs neo4j-0711          # View logs"
echo "  docker exec -it neo4j-0711 bash # Shell access"
echo "  docker exec neo4j-0711 cypher-shell -u neo4j -p ${NEO4J_PASSWORD} # Cypher shell"
echo ""
echo "Test Connection:"
echo "  docker exec neo4j-0711 cypher-shell -u neo4j -p ${NEO4J_PASSWORD} \"RETURN 'Connected!' as status\""
echo ""
echo "=========================================="

# Create initial constraints for 0711-OS
echo ""
echo "Creating initial constraints for 0711-OS..."
docker exec neo4j-0711 cypher-shell -u neo4j -p ${NEO4J_PASSWORD} "
  CREATE CONSTRAINT customer_id IF NOT EXISTS FOR (c:Customer) REQUIRE c.id IS UNIQUE;
  CREATE CONSTRAINT product_id IF NOT EXISTS FOR (p:Product) REQUIRE (p.id, p.client) IS UNIQUE;
  CREATE INDEX product_client IF NOT EXISTS FOR (p:Product) ON (p.client);
" 2>/dev/null || echo "Note: Some constraints may already exist"

echo ""
echo "✓ Setup complete! Neo4j is ready for Bosch migration."
echo ""
