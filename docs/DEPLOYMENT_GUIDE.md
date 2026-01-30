# 0711 Platform - Complete Deployment Guide

**Version:** 2.0.0
**Date:** 2025-01-27

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Installation](#installation)
5. [Migration from Legacy](#migration)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)

---

## Overview

This guide covers the complete deployment of the 0711 platform with the new Cradle-based architecture.

### What's New in V2

- ✅ Centralized GPU processing (Cradle)
- ✅ Stateless MCP services
- ✅ Installation parameters (golden source)
- ✅ Orchestrator MCP (central brain)
- ✅ MCP Marketplace integration
- ✅ Zero data retention in central services

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│  CENTRAL (0711.io Server)                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │   Cradle    │  │ MCP Central │  │  Orchestrator   │  │
│  │  (GPU H200) │  │   (API)     │  │      MCP        │  │
│  └─────────────┘  └─────────────┘  └─────────────────┘  │
└──────────────────────────────────────────────────────────┘
                        │
                        │ Network
                        │
┌───────────────────────┴───────────────────────────────────┐
│  CUSTOMER DEPLOYMENTS (Docker)                            │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐            │
│  │   EATON   │  │ Lightnet  │  │ Customer C│            │
│  └───────────┘  └───────────┘  └───────────┘            │
└───────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### System Requirements

- Ubuntu 22.04 LTS or newer
- 64 GB RAM minimum (for GPU processing)
- 500 GB SSD storage
- NVIDIA GPU (H200, A100, or better)
- CUDA 12.1+

### Software Requirements

```bash
# Docker
docker --version  # 24.x or newer

# Docker Compose
docker compose version  # 2.x or newer

# NVIDIA Container Toolkit
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# PostgreSQL Client
psql --version  # 16.x

# Python
python3 --version  # 3.11+
```

### Installation

```bash
# Docker
curl -fsSL https://get.docker.com | sh

# Docker Compose
sudo apt install docker-compose-plugin

# NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

---

## Installation

### Step 1: Clone Repository

```bash
cd /home/christoph.bertsch/0711
git clone https://github.com/0711/0711-OS.git  # or download
cd 0711-OS
```

### Step 2: Configure Environment

```bash
# Main platform
cp .env.example .env
nano .env  # Edit configuration

# Cradle
cd ../0711-cradle
cp .env.example .env
nano .env

# MCP Central
cd ../0711-mcp-central
cp .env.example .env
nano .env
```

### Step 3: Build Base Image

```bash
cd /home/christoph.bertsch/0711/docker-images/base
./build.sh
```

Expected output:
```
✓ Build complete!
  Image: 0711-base:latest
  Size: 1.2GB
  Saved: 0711-base-latest.tar
```

### Step 4: Start Services

```bash
cd /home/christoph.bertsch/0711/0711-OS

# Start everything
./scripts/start_all_new_architecture.sh
```

This will start:
1. Infrastructure (Postgres, Redis, MinIO)
2. Cradle (GPU Services)
3. MCP Central
4. Platform API

### Step 5: Verify Installation

```bash
# Check all services
curl http://localhost:4080/health  # Platform API
curl http://localhost:4090/health  # MCP Central
curl http://localhost:8001/health  # Cradle Embeddings
curl http://localhost:8002/health  # Cradle Vision

# Check databases
PGPASSWORD=0711_secret psql -h localhost -p 4005 -U 0711_user -d 0711_db -c "SELECT 1"
PGPASSWORD=cradle_secret_2025 psql -h localhost -p 5433 -U cradle -d installation_configs -c "SELECT 1"
PGPASSWORD=mcp_central_secret psql -h localhost -p 5434 -U mcp_central -d user_registry -c "SELECT 1"
```

---

## Migration from Legacy

### EATON Migration

```bash
# Prerequisites
# - Legacy EATON deployment exists at /deployments/eaton
# - Cradle and MCP Central running

./scripts/migrate_eaton.sh
```

**What happens:**
1. **Backup** - Legacy deployment saved
2. **Staging** - Data copied to Cradle
3. **Processing** - GPU processing (embeddings, vision, graph)
4. **Image Build** - Docker image with baked-in data
5. **Deployment** - New architecture deployed
6. **Archive** - Initial image saved (NEVER DELETE!)
7. **Testing** - Health checks and validation

**Duration:** 30-60 minutes (depends on data size)

**Result:**
```
/home/christoph.bertsch/0711/
├── deployments/
│   ├── eaton/                              # New deployment
│   ├── eaton-backup-YYYYMMDD/              # Legacy backup
│   └── archives/
│       ├── eaton-legacy-YYYYMMDD.tar.gz    # Legacy archive
│       └── eaton-v1.0-YYYYMMDD.tar.gz      # New deployment
├── docker-images/versions/eaton/
│   ├── v1.0-init.tar                       # NEVER DELETE!
│   └── v1.0-init.manifest.json             # Metadata
└── 0711-cradle/installation_db/configs/
    └── eaton.json                           # Installation parameters
```

### Lightnet Migration

```bash
./scripts/migrate_lightnet.sh
```

Same process as EATON.

---

## Testing

### Infrastructure Tests

```bash
# PostgreSQL
PGPASSWORD=0711_secret psql -h localhost -p 4005 -U 0711_user -d 0711_db \
  -c "SELECT COUNT(*) FROM customers;"

# Cradle Embedding
curl -X POST http://localhost:8001/embed \
  -H "Content-Type: application/json" \
  -d '{"texts": ["Test document"]}'

# MCP Central
curl http://localhost:4090/api/marketplace/stats
```

### EATON Tests

```bash
# Load token
EATON_TOKEN=$(cat /tmp/eaton-user-token.txt)

# Health
curl http://localhost:9302/health | jq '.'

# Stats
curl http://localhost:9302/stats | jq '.'

# Query test
curl -X POST http://localhost:4080/api/orchestrator/query-database \
  -H "Authorization: Bearer $EATON_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "eaton",
    "database": "lakehouse",
    "query": "SELECT * FROM documents LIMIT 5",
    "require_approval": false
  }' | jq '.'

# Marketplace
curl http://localhost:4090/api/orchestrator/marketplace/mcps \
  -H "Authorization: Bearer $EATON_TOKEN" | jq '.'

# MCP Query (ETIM)
curl -X POST http://localhost:4090/api/orchestrator/marketplace/query \
  -H "Authorization: Bearer $EATON_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mcp_name": "etim",
    "query": "Test query",
    "context": {}
  }' | jq '.'
```

### Lightnet Tests

Same as EATON but with:
- Port 9303 (Lakehouse)
- Lightnet token from `/tmp/lightnet-user-token.txt`

---

## Troubleshooting

### Cradle Services Not Starting

**Symptom:** `curl http://localhost:8001/health` fails

**Solutions:**
```bash
# Check GPU
nvidia-smi

# Check containers
docker-compose -f /home/christoph.bertsch/0711/0711-cradle/docker-compose.cradle.yml ps

# Check logs
docker logs cradle-embeddings
docker logs cradle-vision

# Restart
cd /home/christoph.bertsch/0711/0711-cradle
docker-compose down
docker-compose up -d
```

### MCP Central Not Responding

**Symptom:** `curl http://localhost:4090/health` fails

**Solutions:**
```bash
# Check container
docker ps | grep mcp-central

# Check logs
docker logs mcp-central-api

# Check database
PGPASSWORD=mcp_central_secret psql -h localhost -p 5434 -U mcp_central -d user_registry -c "SELECT COUNT(*) FROM users;"

# Restart
cd /home/christoph.bertsch/0711/0711-mcp-central
docker-compose down
docker-compose up -d
```

### Migration Failed

**Symptom:** `./scripts/migrate_eaton.sh` fails

**Check:**
1. Cradle services running
2. MCP Central running
3. Orchestrator MCP loaded
4. Source data exists

**Rollback:**
```bash
cd /home/christoph.bertsch/0711/deployments

# Stop new deployment
cd eaton
docker-compose down

# Restore backup
cd ..
rm -rf eaton
cp -r eaton-backup-YYYYMMDD eaton

# Start legacy
cd eaton
docker-compose up -d
```

### Customer Deployment Not Starting

**Symptom:** Docker containers not starting

**Solutions:**
```bash
cd /home/christoph.bertsch/0711/deployments/eaton

# Check logs
docker-compose logs

# Check individual services
docker-compose logs neo4j
docker-compose logs lakehouse
docker-compose logs minio

# Restart specific service
docker-compose restart lakehouse
```

### Out of Disk Space

**Check:**
```bash
df -h

# Find large files
du -sh /home/christoph.bertsch/0711/* | sort -h

# Clean up old backups (KEEP versions/ directory!)
cd /home/christoph.bertsch/0711/deployments/archives
ls -lth | head -20  # Review old archives

# Clean Docker
docker system prune -a --volumes  # WARNING: Removes unused data
```

---

## Monitoring

### Service Health Dashboard

```bash
#!/bin/bash
# Save as: scripts/health_dashboard.sh

echo "0711 Platform Health Dashboard"
echo "========================================"
echo ""

# Infrastructure
echo "Infrastructure:"
curl -s http://localhost:4080/health | jq -r '.status' | sed 's/^/  Platform API: /'
curl -s http://localhost:4090/health | jq -r '.status' | sed 's/^/  MCP Central: /'
curl -s http://localhost:8001/health | jq -r '.status' | sed 's/^/  Cradle Embed: /'
curl -s http://localhost:8002/health | jq -r '.status' | sed 's/^/  Cradle Vision: /'

echo ""
echo "Customers:"
curl -s http://localhost:9302/health 2>/dev/null | jq -r '.status' | sed 's/^/  EATON: /' || echo "  EATON: offline"
curl -s http://localhost:9303/health 2>/dev/null | jq -r '.status' | sed 's/^/  Lightnet: /' || echo "  Lightnet: offline"

echo ""
echo "Docker Containers:"
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "cradle|mcp-central|eaton|lightnet"

echo ""
```

### Logs

```bash
# Platform API
tail -f /tmp/platform-api.log

# Cradle
docker logs -f cradle-embeddings

# MCP Central
docker logs -f mcp-central-api

# EATON
cd /home/christoph.bertsch/0711/deployments/eaton
docker-compose logs -f
```

---

## Maintenance

### Daily Tasks

```bash
# Health check
./scripts/health_dashboard.sh

# Check disk space
df -h

# Check GPU
nvidia-smi
```

### Weekly Tasks

```bash
# Database backups
pg_dump -h localhost -p 4005 -U 0711_user 0711_db > backup-$(date +%Y%m%d).sql

# Archive old logs
find /tmp -name "*.log" -mtime +7 -delete
```

### Monthly Tasks

```bash
# Review archives
du -sh /home/christoph.bertsch/0711/deployments/archives/*

# Clean old staging
rm -rf /home/christoph.bertsch/0711/0711-cradle/staging/*

# Update Docker images
docker pull nvidia/cuda:12.1.0-base-ubuntu22.04
```

---

## Backup & Recovery

### What to Backup

**CRITICAL (Daily):**
- PostgreSQL databases (all 3)
- Customer data volumes
- Installation configs

**IMPORTANT (Weekly):**
- Deployment configurations
- User registry

**ARCHIVE (Permanent):**
- Initial Docker images (versions/)
- Deployment archives

### Backup Script

```bash
#!/bin/bash
# Save as: scripts/backup.sh

BACKUP_DIR="/backup/0711-$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# Databases
pg_dump -h localhost -p 4005 -U 0711_user 0711_db > "$BACKUP_DIR/platform.sql"
pg_dump -h localhost -p 5433 -U cradle installation_configs > "$BACKUP_DIR/installation.sql"
pg_dump -h localhost -p 5434 -U mcp_central user_registry > "$BACKUP_DIR/users.sql"

# Customer volumes
docker run --rm -v eaton-lakehouse-data:/data -v "$BACKUP_DIR":/backup \
  ubuntu tar czf /backup/eaton-lakehouse.tar.gz /data

# Config files
cp -r /home/christoph.bertsch/0711/0711-cradle/installation_db/configs "$BACKUP_DIR/"

echo "Backup complete: $BACKUP_DIR"
```

### Recovery

```bash
# Restore database
psql -h localhost -p 4005 -U 0711_user 0711_db < backup-YYYYMMDD.sql

# Restore volume
docker run --rm -v eaton-lakehouse-data:/data -v /backup:/backup \
  ubuntu tar xzf /backup/eaton-lakehouse.tar.gz -C /
```

---

## Customer Delivery

### Create Delivery Package

```bash
# EATON
./scripts/create_customer_delivery.sh eaton 1.0

# Lightnet
./scripts/create_customer_delivery.sh lightnet 1.0
```

**Package contents:**
```
customer-deliveries/eaton/
├── eaton-v1.0-image.tar              # Docker image (2.7 GB)
├── eaton-v1.0-deployment.tar.gz      # Deployment files
├── docker-compose.yml                # Service orchestration
├── .env.template                     # Environment template
├── credentials.txt                   # Access credentials
├── INSTALLATION_GUIDE.md             # Customer instructions
└── eaton-v1.0-manifest.json          # Metadata
```

### Delivery to Customer

1. **Upload to secure storage:**
   ```bash
   # To S3/MinIO
   mc cp customer-deliveries/eaton/* s3://0711-customer-delivery/eaton/

   # Generate download link (expires in 7 days)
   mc share download --expire=168h s3://0711-customer-delivery/eaton/
   ```

2. **Send to customer:**
   - Download link
   - Installation guide
   - Support contact

3. **Customer installs:**
   - Downloads package
   - Runs `docker load -i eaton-v1.0-image.tar`
   - Starts with `docker-compose up -d`
   - Connects to 0711 MCP Central

---

## Scaling

### Adding More Customers

```bash
# For customer #3
curl -X POST http://localhost:4090/api/orchestrator/initialize-customer \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "New Customer",
    "contact_email": "admin@newcustomer.com",
    "data_sources": ["/data/import"],
    "deployment_target": "on-premise"
  }'
```

### Adding More GPUs

```yaml
# In 0711-cradle/docker-compose.cradle.yml

services:
  embedding-service-2:
    # ... same as embedding-service
    container_name: cradle-embeddings-gpu2
    ports:
      - "8011:8000"  # Different port
    environment:
      - CUDA_VISIBLE_DEVICES=2  # Different GPU
    deploy:
      resources:
        reservations:
          devices:
            - device_ids: ['2']  # GPU 2
```

### Horizontal Scaling (MCP Central)

```yaml
# Multiple MCP Central instances behind load balancer

services:
  mcp-central-api-1:
    # ... existing config
    container_name: mcp-central-api-1

  mcp-central-api-2:
    # ... existing config
    container_name: mcp-central-api-2
    ports:
      - "4091:8000"  # Different external port

  nginx:
    image: nginx
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    ports:
      - "4090:80"  # Load balancer
```

---

## Security

### Production Checklist

- [ ] Change all default passwords
- [ ] Use HTTPS (not HTTP)
- [ ] Enable firewall rules
- [ ] Restrict database access
- [ ] Enable audit logging
- [ ] Set up backup automation
- [ ] Configure monitoring/alerting
- [ ] Review user permissions

### Secrets Management

```bash
# Use environment variables
export JWT_SECRET=$(openssl rand -hex 32)
export POSTGRES_PASSWORD=$(openssl rand -hex 16)

# Or use secrets manager (production)
# - HashiCorp Vault
# - AWS Secrets Manager
# - Azure Key Vault
```

---

## Appendix

### Directory Structure

```
/home/christoph.bertsch/0711/
├── 0711-OS/                      # Main platform
├── 0711-cradle/                  # GPU processing
├── 0711-mcp-central/             # Central services
├── deployments/                  # Customer deployments
│   ├── eaton/
│   ├── lightnet/
│   └── archives/
├── docker-images/                # Images
│   ├── base/
│   ├── customer/
│   └── versions/                 # NEVER DELETE!
└── customer-deliveries/          # For customers
```

### Port Allocation

| Range | Purpose |
|-------|---------|
| 4000-4099 | Platform services |
| 5000-5999 | Databases |
| 7000-7999 | Customer services (Neo4j, etc.) |
| 8000-8999 | Cradle services |
| 9000-9999 | Customer APIs (Lakehouse, MinIO) |

### Environment Variables Reference

See `.env.example` files in each directory.

---

**Built with ❤️ by 0711 Intelligence**
