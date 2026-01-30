#!/bin/bash
# EATON Migration Script
# Migrates EATON from legacy architecture to new Cradle-based architecture

set -e

CUSTOMER_ID="eaton"
COMPANY_NAME="EATON"
CONTACT_EMAIL="max@eaton.com"
DEPLOYMENT_TARGET="on-premise"

echo "=========================================="
echo "EATON Migration to New Architecture"
echo "=========================================="
echo ""

# Step 1: Backup current deployment
echo "Step 1: Backing up current EATON deployment..."
cd /home/christoph.bertsch/0711/deployments

if [ ! -d "eaton" ]; then
    echo "Error: EATON deployment not found"
    exit 1
fi

# Stop containers
echo "  Stopping EATON containers..."
cd eaton
docker-compose down

# Backup
cd ..
BACKUP_DIR="eaton-backup-$(date +%Y%m%d-%H%M%S)"
echo "  Creating backup: $BACKUP_DIR"
sudo cp -r eaton "$BACKUP_DIR"

# Archive legacy
echo "  Archiving legacy deployment..."
mkdir -p archives
tar -czf "archives/eaton-legacy-$(date +%Y%m%d).tar.gz" "$BACKUP_DIR"

# Save container images (if needed)
echo "  Saving Docker images..."
if docker images | grep -q "eaton-vllm"; then
    docker save eaton-vllm:latest -o "archives/eaton-vllm-legacy-$(date +%Y%m%d).tar"
fi

if docker images | grep -q "eaton-lakehouse"; then
    docker save eaton-lakehouse:latest -o "archives/eaton-lakehouse-legacy-$(date +%Y%m%d).tar"
fi

echo "✓ Backup complete"
echo ""

# Step 2: Extract existing data to Cradle staging
echo "Step 2: Preparing data for Cradle processing..."

STAGING_DIR="/home/christoph.bertsch/0711/0711-cradle/staging/$CUSTOMER_ID"
mkdir -p "$STAGING_DIR"

# Copy MinIO data (if available)
if [ -d "$BACKUP_DIR/data/minio" ]; then
    echo "  Copying MinIO data..."
    cp -r "$BACKUP_DIR/data/minio/"* "$STAGING_DIR/" 2>/dev/null || true
fi

# Alternative: Download from MinIO container
echo "  Downloading from MinIO..."
docker exec 0711-minio mc mirror /data/customer-eaton "$STAGING_DIR/" 2>/dev/null || true

FILE_COUNT=$(find "$STAGING_DIR" -type f | wc -l)
echo "✓ Prepared $FILE_COUNT files for processing"
echo ""

# Step 3: Initialize via Orchestrator
echo "Step 3: Initializing via Orchestrator API..."
echo "  (This will take 10-30 minutes - processing with Cradle GPU)"

# Create initialization request
cat > /tmp/eaton-init.json <<EOF
{
  "company_name": "$COMPANY_NAME",
  "contact_email": "$CONTACT_EMAIL",
  "data_sources": ["$STAGING_DIR"],
  "deployment_target": "$DEPLOYMENT_TARGET",
  "mcps": ["ctax", "law", "etim"],
  "installation_params": {
    "embedding_model": "intfloat/multilingual-e5-large",
    "embedding_batch_size": 128,
    "vision_enabled": true,
    "graph_extraction_enabled": true
  }
}
EOF

# Call Orchestrator API
echo "  Calling: POST http://localhost:4090/api/orchestrator/initialize-customer"
RESPONSE=$(curl -s -X POST http://localhost:4090/api/orchestrator/initialize-customer \
    -H "Content-Type: application/json" \
    -d @/tmp/eaton-init.json)

echo "$RESPONSE" | jq '.' > /tmp/eaton-init-response.json

if echo "$RESPONSE" | jq -e '.success' > /dev/null; then
    echo "✓ Initialization successful"
    USER_TOKEN=$(echo "$RESPONSE" | jq -r '.data.user_token')
    echo "  User Token: $USER_TOKEN"
    echo "$USER_TOKEN" > /tmp/eaton-user-token.txt
else
    echo "✗ Initialization failed"
    echo "$RESPONSE" | jq '.'
    exit 1
fi

echo ""

# Step 4: Verify deployment
echo "Step 4: Verifying deployment..."

# Wait for services to start
echo "  Waiting for services to start (30 seconds)..."
sleep 30

# Health check
echo "  Checking health..."
curl -s http://localhost:9302/health | jq '.'

# Stats check
echo "  Checking stats..."
curl -s http://localhost:9302/stats | jq '.'

echo "✓ Deployment verified"
echo ""

# Step 5: Archive initial image
echo "Step 5: Archiving initial image..."

VERSIONS_DIR="/home/christoph.bertsch/0711/docker-images/versions/$CUSTOMER_ID"
if [ -d "$VERSIONS_DIR" ]; then
    echo "  Initial image archived at: $VERSIONS_DIR/v1.0-init.tar"
    ls -lh "$VERSIONS_DIR/"
else
    echo "  Warning: Versions directory not found"
fi

echo "✓ Initial image archived (NEVER DELETE!)"
echo ""

# Step 6: Create deployment archive
echo "Step 6: Creating deployment archive..."

cd /home/christoph.bertsch/0711/deployments
tar -czf "archives/eaton-v1.0-$(date +%Y%m%d).tar.gz" eaton/

echo "✓ Deployment archive created"
echo ""

# Done!
echo "=========================================="
echo "EATON Migration Complete!"
echo "=========================================="
echo ""
echo "Summary:"
echo "  - Legacy backup: $BACKUP_DIR"
echo "  - New deployment: /home/christoph.bertsch/0711/deployments/eaton"
echo "  - Initial image: /home/christoph.bertsch/0711/docker-images/versions/eaton/v1.0-init.tar"
echo "  - User token: /tmp/eaton-user-token.txt"
echo ""
echo "Access:"
echo "  - Console: http://localhost:4020"
echo "  - Lakehouse: http://localhost:9302"
echo "  - Neo4j: neo4j://localhost:7687"
echo ""
echo "Next steps:"
echo "  1. Test console login"
echo "  2. Verify data integrity"
echo "  3. Test MCP marketplace"
echo ""
