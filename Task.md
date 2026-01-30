# Task: Deploy 0711-OS Platform on H200

**Priority:** High  
**Assigned:** Claude Code (H200)  
**Status:** In Progress
**Updated:** 2026-01-30

---

## 🚀 LATEST UPDATE

Major refactor just pushed! New features:
1. **MCP → Connector rename** - Better terminology
2. **Dynamic marketplace** - Real database-driven marketplace
3. **Expert booking system** - Full freelancer marketplace with payments

**After deploying, run:**
```bash
# Run database migration
cd ~/OS
source venv/bin/activate  # or use Docker
alembic upgrade head

# Seed marketplace data (categories + sample connectors)
python scripts/seed_marketplace.py
```

---

## Objective

Deploy the complete 0711-OS platform on this H200 server with GPU acceleration for vLLM.

## Prerequisites Check

First, verify the environment:

```bash
# Check GPU
nvidia-smi

# Check Docker
docker --version
docker compose version

# Check available disk space
df -h

# Check memory
free -h
```

## Step 1: Clone/Update Repository

```bash
cd ~
if [ -d "OS" ]; then
    cd OS && git pull origin main
else
    git clone https://github.com/christoph-ui/OS.git
    cd OS
fi
```

## Step 2: Create Environment File

```bash
cp .env.example .env
```

Edit `.env` with these critical settings:

```bash
# Database
DATABASE_URL=postgresql://os711:os711secret@postgres:5432/os711

# Redis
REDIS_URL=redis://redis:6379

# MinIO
MINIO_URL=http://minio:9000
MINIO_ACCESS_KEY=0711admin
MINIO_SECRET_KEY=0711secret

# vLLM (local GPU)
VLLM_URL=http://vllm:8000

# Embeddings
EMBEDDINGS_URL=http://embeddings:8001

# Model config
VLLM_MODEL=Qwen/Qwen2.5-72B-Instruct
HF_TOKEN=<ADD_YOUR_HF_TOKEN>

# API Keys (optional - for Claude-powered adaptive ingestion)
ANTHROPIC_API_KEY=<ADD_IF_AVAILABLE>

# Development
DEBUG=true
DEPLOYMENT_TYPE=development
```

## Step 3: Start with Docker Compose

Use the H200-optimized docker-compose:

```bash
# Start infrastructure
docker compose -f docker-compose.yml up -d postgres redis minio

# Wait for healthy
sleep 10

# Run migrations
docker compose run --rm api alembic upgrade head

# Seed marketplace data
docker compose run --rm api python scripts/seed_marketplace.py

# Start AI services (this downloads models - takes time!)
docker compose up -d vllm embeddings

# Monitor vLLM startup
docker compose logs -f vllm

# Once vLLM shows "Application startup complete", start app
docker compose up -d api console-backend console-frontend website
```

## Step 4: Verify Deployment

```bash
# Check all containers
docker compose ps

# Test endpoints
curl http://localhost:4080/health
curl http://localhost:4010/health
curl http://localhost:8000/health  # vLLM
curl http://localhost:8001/health  # Embeddings

# Test new marketplace API
curl http://localhost:4080/api/connectors | jq
curl http://localhost:4080/api/connectors/categories | jq
curl http://localhost:4080/api/connectors/featured | jq

# Check GPU utilization
nvidia-smi
```

## Step 5: Report Back

Once deployed, update this file with:
- [ ] GPU info (nvidia-smi output)
- [ ] Container status (docker ps)
- [ ] Health check results
- [ ] Marketplace API responses
- [ ] Any errors encountered
- [ ] Access URLs

---

## New API Endpoints (after refactor)

### Connector Marketplace
```
GET  /api/connectors                    # Search/browse connectors
GET  /api/connectors/categories         # Category tree
GET  /api/connectors/featured           # Featured connectors
GET  /api/connectors/trending           # Trending connectors
GET  /api/connectors/{id}               # Connector details
GET  /api/connectors/{id}/reviews       # Reviews
POST /api/connectors/{id}/install       # Install connector
POST /api/connectors/{id}/reviews       # Leave review
```

### Expert Booking
```
POST /api/bookings                      # Create booking request
GET  /api/bookings/my                   # Customer's bookings
POST /api/bookings/{id}/confirm         # Confirm booking

# Expert endpoints
GET  /api/expert/bookings               # Expert's bookings
POST /api/expert/bookings/{id}/accept   # Accept booking
POST /api/expert/bookings/{id}/decline  # Decline booking

# Availability
GET  /api/experts/{id}/availability     # Get schedule
PUT  /api/experts/{id}/availability     # Set schedule
```

---

## Expected Access Points

After successful deployment:

| Service | URL |
|---------|-----|
| Console (Chat) | http://<H200_IP>:4020 |
| Marketing Site | http://<H200_IP>:4000 |
| API Docs | http://<H200_IP>:4080/docs |
| MinIO Console | http://<H200_IP>:9001 |
| vLLM API | http://<H200_IP>:8000 |

---

**Note:** If HF_TOKEN is not set, vLLM won't be able to download gated models. Get token from https://huggingface.co/settings/tokens

## Deployment Status

_Update this section after deployment:_

```
Status: PENDING
GPU: 
Containers: 
API Health: 
Marketplace: 
Notes: 
```
