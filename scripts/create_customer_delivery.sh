#!/bin/bash
# Create Customer Delivery Package
# Packages all files needed for customer deployment

set -e

CUSTOMER_ID=$1
VERSION=${2:-"1.0"}

if [ -z "$CUSTOMER_ID" ]; then
    echo "Usage: $0 <customer_id> [version]"
    echo "Example: $0 eaton 1.0"
    exit 1
fi

echo "=========================================="
echo "Creating delivery package for: $CUSTOMER_ID"
echo "=========================================="
echo ""

DELIVERY_DIR="/home/christoph.bertsch/0711/customer-deliveries/$CUSTOMER_ID"
VERSIONS_DIR="/home/christoph.bertsch/0711/docker-images/versions/$CUSTOMER_ID"
DEPLOYMENT_DIR="/home/christoph.bertsch/0711/deployments/$CUSTOMER_ID"

# Create delivery directory
mkdir -p "$DELIVERY_DIR"

# Step 1: Copy Docker image
echo "Step 1: Copying Docker image..."

if [ ! -f "$VERSIONS_DIR/v$VERSION-init.tar" ]; then
    echo "Error: Initial image not found: $VERSIONS_DIR/v$VERSION-init.tar"
    exit 1
fi

cp "$VERSIONS_DIR/v$VERSION-init.tar" "$DELIVERY_DIR/$CUSTOMER_ID-v$VERSION-image.tar"

IMAGE_SIZE=$(du -h "$DELIVERY_DIR/$CUSTOMER_ID-v$VERSION-image.tar" | cut -f1)
echo "✓ Image copied ($IMAGE_SIZE)"
echo ""

# Step 2: Copy manifest
echo "Step 2: Copying manifest..."
cp "$VERSIONS_DIR/v$VERSION-init.manifest.json" "$DELIVERY_DIR/$CUSTOMER_ID-v$VERSION-manifest.json"
echo "✓ Manifest copied"
echo ""

# Step 3: Create deployment archive
echo "Step 3: Creating deployment archive..."

if [ ! -d "$DEPLOYMENT_DIR" ]; then
    echo "Error: Deployment directory not found: $DEPLOYMENT_DIR"
    exit 1
fi

cd /home/christoph.bertsch/0711/deployments
tar -czf "$DELIVERY_DIR/$CUSTOMER_ID-v$VERSION-deployment.tar.gz" "$CUSTOMER_ID/"

DEPLOY_SIZE=$(du -h "$DELIVERY_DIR/$CUSTOMER_ID-v$VERSION-deployment.tar.gz" | cut -f1)
echo "✓ Deployment archive created ($DEPLOY_SIZE)"
echo ""

# Step 4: Copy docker-compose.yml
echo "Step 4: Copying deployment files..."
cp "$DEPLOYMENT_DIR/docker-compose.yml" "$DELIVERY_DIR/"
cp "$DEPLOYMENT_DIR/.env" "$DELIVERY_DIR/.env.template"
echo "✓ Deployment files copied"
echo ""

# Step 5: Generate credentials file
echo "Step 5: Generating credentials..."

cat > "$DELIVERY_DIR/credentials.txt" <<EOF
0711 Intelligence Platform - Credentials
Customer: $CUSTOMER_ID
Version: v$VERSION
Generated: $(date +"%Y-%m-%d %H:%M:%S")

========================================
IMPORTANT: Keep these credentials secure!
========================================

Console Access:
  URL: http://localhost:4020
  Email: (from .env file)
  Password: (from .env file)

Database Credentials:
  Neo4j: neo4j / (see .env: NEO4J_AUTH)
  PostgreSQL: (see .env: POSTGRES_PASSWORD)
  MinIO: (see .env: MINIO_ROOT_USER / MINIO_ROOT_PASSWORD)

0711 MCP Central:
  User Token: (see .env: USER_TOKEN)
  API URL: http://localhost:4090

Support:
  Email: support@0711.io
  Docs: https://docs.0711.io
  Emergency: +49 711 XXX XXXX

========================================
EOF

echo "✓ Credentials file generated"
echo ""

# Step 6: Generate installation guide
echo "Step 6: Generating installation guide..."

cat > "$DELIVERY_DIR/INSTALLATION_GUIDE.md" <<'EOF'
# 0711 Intelligence Platform - Installation Guide

## Customer: $CUSTOMER_ID
## Version: v$VERSION

---

## Package Contents

- `$CUSTOMER_ID-v$VERSION-image.tar` - Docker image with pre-loaded data
- `$CUSTOMER_ID-v$VERSION-deployment.tar.gz` - Deployment configuration
- `docker-compose.yml` - Service orchestration
- `.env.template` - Environment variables template
- `credentials.txt` - Access credentials
- `INSTALLATION_GUIDE.md` - This file

---

## Pre-Requisites

### System Requirements
- **OS:** Ubuntu 22.04 / Debian 12 / RHEL 9
- **RAM:** 16 GB minimum, 32 GB recommended
- **Storage:** 50 GB SSD minimum
- **CPU:** 4 cores minimum, 8 cores recommended

### Software Requirements
- Docker 24.x or newer
- Docker Compose 2.x or newer

### Installation
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt-get install docker-compose-plugin

# Verify
docker --version
docker compose version
```

---

## Installation Steps

### 1. Load Docker Image

Extract the package and load the Docker image:

```bash
# Load image
docker load -i $CUSTOMER_ID-v$VERSION-image.tar

# Verify
docker images | grep $CUSTOMER_ID
```

### 2. Extract Deployment Files

```bash
# Extract deployment configuration
tar -xzf $CUSTOMER_ID-v$VERSION-deployment.tar.gz

# Navigate to deployment directory
cd $CUSTOMER_ID
```

### 3. Configure Environment

```bash
# Copy environment template
cp .env.template .env

# Review and update if needed
nano .env
```

### 4. Start Services

```bash
# Start all services
docker-compose up -d

# Verify services are running
docker-compose ps
```

Expected output:
```
NAME                    STATUS
$CUSTOMER_ID-neo4j      Up
$CUSTOMER_ID-lakehouse  Up
$CUSTOMER_ID-minio      Up
$CUSTOMER_ID-console    Up
```

### 5. Verify Deployment

```bash
# Health check
curl http://localhost:9302/health

# Expected response:
# {
#   "status": "healthy",
#   "documents": XXXXX,
#   "embeddings": XXXXX
# }

# Stats check
curl http://localhost:9302/stats
```

---

## Accessing the Platform

### Console UI

Open in browser:
```
http://localhost:4020
```

Login with credentials from `credentials.txt`

### API Access

All customer APIs are available:

```bash
# Lakehouse API
curl http://localhost:9302/health

# Stats API
curl http://localhost:4020/api/stats
```

---

## Connection to 0711 MCP Central

Your deployment is automatically connected to 0711 MCP Central for:

- **Embedding generation** (incremental updates)
- **Vision/OCR services** (new images)
- **MCP Marketplace access** (install additional MCPs)
- **Continuous learning** (V2)

**Authentication:**
- User Token: (see `.env` file or `credentials.txt`)
- MCP Central URL: http://localhost:4090 (or https://mcp.0711.io in production)

### Test Connection

```bash
# Load token from .env
source .env

# Test marketplace
curl http://localhost:4090/api/orchestrator/marketplace/mcps \
  -H "Authorization: Bearer $USER_TOKEN"
```

---

## Updating Data

### Upload New Files

Upload via Console UI or API:

```bash
curl -X POST http://localhost:4020/api/upload/files \
  -H "Authorization: Bearer $USER_TOKEN" \
  -F "files=@document.pdf"
```

### Process New Documents

Embeddings are automatically offered when new documents are detected.

Or trigger manually:

```bash
curl -X POST http://localhost:4090/api/orchestrator/process-documents \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "$CUSTOMER_ID",
    "file_paths": ["/data/new-document.pdf"]
  }'
```

---

## Troubleshooting

### Services not starting

```bash
# Check logs
docker-compose logs

# Check specific service
docker-compose logs lakehouse
```

### Connection to MCP Central failing

```bash
# Verify token
echo $USER_TOKEN

# Test MCP Central
curl http://localhost:4090/health
```

### Data not showing

```bash
# Check lakehouse
curl http://localhost:9302/stats

# Check MinIO
docker exec $CUSTOMER_ID-minio mc ls /data/
```

---

## Support

**Email:** support@0711.io
**Documentation:** https://docs.0711.io
**Emergency:** +49 711 XXX XXXX

**Business Hours:** Mon-Fri 9:00-18:00 CET

---

## Appendix

### Service Ports

| Service | Port | Description |
|---------|------|-------------|
| Neo4j Bolt | 7687 | Graph database |
| Neo4j Browser | 7474 | Web UI |
| Lakehouse API | 9302 | Data access |
| MinIO API | 9000 | Object storage |
| MinIO Console | 9001 | Web UI |
| Console | 4020 | Main UI |

### Data Volumes

All data is stored in Docker volumes:

```bash
# List volumes
docker volume ls | grep $CUSTOMER_ID

# Backup volume
docker run --rm -v $CUSTOMER_ID-lakehouse-data:/data \
  -v /backup:/backup \
  ubuntu tar czf /backup/$CUSTOMER_ID-lakehouse-$(date +%Y%m%d).tar.gz /data
```

---

**Installation Date:** _________________
**Installed By:** _________________
**Notes:** _________________________________________________________________

---

**Built with ❤️ by 0711 Intelligence**
EOF

# Replace placeholders
sed -i "s/\$CUSTOMER_ID/$CUSTOMER_ID/g" "$DELIVERY_DIR/INSTALLATION_GUIDE.md"
sed -i "s/\$VERSION/$VERSION/g" "$DELIVERY_DIR/INSTALLATION_GUIDE.md"

echo "✓ Installation guide generated"
echo ""

# Done!
echo "=========================================="
echo "Customer Delivery Package Complete!"
echo "=========================================="
echo ""
echo "Package location: $DELIVERY_DIR"
echo ""
echo "Contents:"
ls -lh "$DELIVERY_DIR/"
echo ""
echo "Package ready for delivery to customer!"
echo ""
