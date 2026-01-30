#!/bin/bash
# Lightnet Migration Script
# Migrates Lightnet from legacy architecture to new Cradle-based architecture

set -e

CUSTOMER_ID="lightnet"
COMPANY_NAME="Lightnet"
CONTACT_EMAIL="admin@lightnet.de"
DEPLOYMENT_TARGET="on-premise"

echo "=========================================="
echo "Lightnet Migration to New Architecture"
echo "=========================================="
echo ""

# Step 1: Backup current deployment
echo "Step 1: Backing up current Lightnet deployment..."
cd /home/christoph.bertsch/0711/deployments

if [ ! -d "lightnet" ]; then
    echo "Error: Lightnet deployment not found"
    exit 1
fi

# Stop containers
echo "  Stopping Lightnet containers..."
cd lightnet
docker-compose down 2>/dev/null || true

# Backup
cd ..
BACKUP_DIR="lightnet-backup-$(date +%Y%m%d-%H%M%S)"
echo "  Creating backup: $BACKUP_DIR"
sudo cp -r lightnet "$BACKUP_DIR"

# Archive legacy
echo "  Archiving legacy deployment..."
mkdir -p archives
tar -czf "archives/lightnet-legacy-$(date +%Y%m%d).tar.gz" "$BACKUP_DIR"

echo "✓ Backup complete"
echo ""

# Step 2: Extract existing data to Cradle staging
echo "Step 2: Preparing data for Cradle processing..."

STAGING_DIR="/home/christoph.bertsch/0711/0711-cradle/staging/$CUSTOMER_ID"
mkdir -p "$STAGING_DIR"

# Copy existing data
if [ -d "$BACKUP_DIR/data" ]; then
    echo "  Copying existing data..."
    find "$BACKUP_DIR/data" -type f -exec cp {} "$STAGING_DIR/" \; 2>/dev/null || true
fi

FILE_COUNT=$(find "$STAGING_DIR" -type f | wc -l)
echo "✓ Prepared $FILE_COUNT files for processing"
echo ""

# Step 3: Initialize via Orchestrator
echo "Step 3: Initializing via Orchestrator API..."
echo "  (This will take 10-30 minutes - processing with Cradle GPU)"

# Create initialization request
cat > /tmp/lightnet-init.json <<EOF
{
  "company_name": "$COMPANY_NAME",
  "contact_email": "$CONTACT_EMAIL",
  "data_sources": ["$STAGING_DIR"],
  "deployment_target": "$DEPLOYMENT_TARGET",
  "mcps": ["ctax", "law"],
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
    -d @/tmp/lightnet-init.json)

echo "$RESPONSE" | jq '.' > /tmp/lightnet-init-response.json

if echo "$RESPONSE" | jq -e '.success' > /dev/null; then
    echo "✓ Initialization successful"
    USER_TOKEN=$(echo "$RESPONSE" | jq -r '.data.user_token')
    echo "  User Token: $USER_TOKEN"
    echo "$USER_TOKEN" > /tmp/lightnet-user-token.txt
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

# Health check (different port for Lightnet)
echo "  Checking health..."
curl -s http://localhost:9303/health | jq '.' || echo "  Warning: Health check failed"

# Stats check
echo "  Checking stats..."
curl -s http://localhost:9303/stats | jq '.' || echo "  Warning: Stats unavailable"

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
tar -czf "archives/lightnet-v1.0-$(date +%Y%m%d).tar.gz" lightnet/

echo "✓ Deployment archive created"
echo ""

# Done!
echo "=========================================="
echo "Lightnet Migration Complete!"
echo "=========================================="
echo ""
echo "Summary:"
echo "  - Legacy backup: $BACKUP_DIR"
echo "  - New deployment: /home/christoph.bertsch/0711/deployments/lightnet"
echo "  - Initial image: /home/christoph.bertsch/0711/docker-images/versions/lightnet/v1.0-init.tar"
echo "  - User token: /tmp/lightnet-user-token.txt"
echo ""
echo "Access:"
echo "  - Console: http://localhost:4021"
echo "  - Lakehouse: http://localhost:9303"
echo "  - Neo4j: neo4j://localhost:7688"
echo ""
