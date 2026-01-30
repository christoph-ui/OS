# 0711 Platform Deployment Guide

Complete guide to deploying the 0711 Intelligence Orchestration Platform.

## Quick Start

```bash
# 1. Clone repository
git clone https://github.com/0711/platform.git
cd platform

# 2. Run installer
cd provisioning/installer
./install.sh

# 3. Open setup wizard
# Browser will open to: http://localhost:8090
```

---

## What Gets Installed

The 0711 Platform consists of:

### Core Services
- **vLLM Server**: Mixtral-8x7B-Instruct inference
- **MinIO**: S3-compatible object storage
- **Ray Cluster**: Distributed compute for MCPs
- **Lakehouse**: Delta Lake (structured) + Lance (vectors)

### Application Layer
- **Setup Wizard**: Folder selection and ingestion kickoff
- **Ingestion Pipeline**: Crawl → Extract → Classify → Chunk → Embed → Load
- **MCPs**: Specialized AI agents (CTAX, LAW, etc.)
- **Console**: Chat UI and admin interface

---

## Prerequisites

### System Requirements

**Minimum:**
- Ubuntu 22.04 LTS (or similar)
- 16GB RAM
- 100GB free disk space
- Docker 24.0+ with Compose v2

**Recommended:**
- 32GB+ RAM
- 500GB+ SSD
- NVIDIA GPU with 24GB+ VRAM
- nvidia-container-toolkit installed

### API Keys

**Required:**
- **Anthropic API Key**: For adaptive file handler generation
  - Get from: https://console.anthropic.com/
  - Set in wizard or `.env` file

**Optional:**
- None currently (all models run locally)

---

## Installation

### Step 1: Run Installer

```bash
cd provisioning/installer
./install.sh
```

The installer will:
1. ✅ Check prerequisites (Docker, GPU, disk, RAM)
2. ✅ Pull Docker images (~15GB)
3. ✅ Generate secure configuration
4. ✅ Initialize lakehouse storage
5. ✅ Start setup wizard

### Step 2: Setup Wizard

Open http://localhost:8090 in your browser.

#### 2.1 Welcome & System Check
- Reviews system capabilities
- Confirms GPU availability
- Validates configuration

#### 2.2 License Activation
- Enter license key
- Activate deployment

#### 2.3 Folder Selection 📁
**This is the key step!**

1. **Browse your filesystem** to find company data
2. **Select folders** containing documents to ingest:
   - `/data/accounting` → Assign to **CTAX** (tax)
   - `/data/contracts` → Assign to **LAW** (legal)
   - `/data/products` → Assign to **ETIM** (products)
   - `/data/hr` → Assign to **HR**

3. **Review statistics**:
   - Number of files detected
   - Total size
   - File type breakdown
   - Unknown formats (will generate handlers)

4. **Confirm selections**

#### 2.4 Ingestion Progress ⚙️

Watch real-time progress as system:
- **Discovers** all files
- **Extracts** content (using built-in handlers)
- **Generates** custom handlers for unknown formats via Claude
- **Classifies** documents to MCPs
- **Chunks** text intelligently
- **Embeds** with multilingual-e5-large
- **Loads** to lakehouse (Delta + Lance)

This typically takes 1-10 minutes per 1000 documents.

#### 2.5 Launch 🚀
- Starts all platform services
- Verifies health
- Redirects to console

---

## Using the Platform

### Console UI

Access at: http://localhost:3000

#### Chat Interface
Ask questions about your data:

**Examples:**
- "Zeige mir alle Steuerdokumente aus Q3 2023"
- "Welche Verträge laufen 2024 aus?"
- "Liste alle Produkte der Kategorie X"

The system will:
1. Route to appropriate MCP (CTAX, LAW, etc.)
2. Search relevant documents
3. Generate answer with sources
4. Show confidence score

#### Data Browser
- View all ingested documents
- Filter by MCP, date, file type
- See chunk breakdown
- Re-ingest folders

#### MCP Management
- View active MCPs and their data stats
- See query performance
- Manage custom handlers

### API Access

The platform exposes REST and WebSocket APIs:

```bash
# Health check
curl http://localhost:8080/health

# Query an MCP
curl -X POST http://localhost:8080/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "mcp": "ctax",
    "query": "Umsatzsteuer Q3 2023"
  }'

# List documents
curl http://localhost:8080/api/documents?mcp=tax

# WebSocket for streaming
ws://localhost:8080/ws
```

---

## Administration

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f ingestion
docker compose logs -f vllm
docker compose logs -f console-backend

# Last 100 lines
docker compose logs --tail=100 ray-head
```

### Check Status

```bash
# Run health check
./deployment/scripts/health-check.sh

# View running containers
docker compose ps

# View Ray dashboard
open http://localhost:8265

# View MinIO console
open http://localhost:9001
```

### Re-ingest Data

Add more folders:

```bash
# Through console UI
# Or manually trigger ingestion

docker compose run --rm ingestion python -m ingestion.orchestrator \
  /path/to/new/folder \
  --mcp=tax \
  --lakehouse=/app/lakehouse
```

### Backup Data

```bash
# Backup lakehouse (Delta + Lance)
tar -czf lakehouse-backup-$(date +%Y%m%d).tar.gz \
  /opt/0711/data/lakehouse

# Backup configuration
tar -czf config-backup-$(date +%Y%m%d).tar.gz \
  /opt/0711/config
```

### Update Platform

```bash
# Pull latest images
docker compose pull

# Restart services
docker compose down
docker compose up -d

# Check health
./deployment/scripts/health-check.sh
```

---

## Troubleshooting

### Ingestion Fails with Unknown Format

**Problem**: File format not recognized, handler generation fails

**Solution**:
1. Check Claude API key is set: `echo $ANTHROPIC_API_KEY`
2. View ingestion logs: `docker compose logs ingestion`
3. Manually specify format in wizard
4. Generate handler through console UI

### vLLM Out of Memory

**Problem**: GPU runs out of memory during inference

**Solution**:
```bash
# Reduce GPU utilization in .env
GPU_MEMORY_UTILIZATION=0.7

# Or reduce model context length
MAX_MODEL_LEN=16384

# Restart vLLM
docker compose restart vllm
```

### Search Returns No Results

**Problem**: Queries don't find relevant documents

**Possible causes**:
1. **Data not ingested**: Check lakehouse has data
   ```bash
   ls -la /opt/0711/data/lakehouse/delta/
   ls -la /opt/0711/data/lakehouse/lance/
   ```

2. **Wrong MCP**: Query is routing to wrong MCP
   - Check document classification in data browser
   - Try querying different MCPs

3. **Embeddings not generated**: Check ingestion completed
   ```bash
   docker compose logs ingestion | grep "Embedding"
   ```

### Services Won't Start

**Check prerequisites**:
```bash
# Docker running?
docker ps

# Enough disk space?
df -h /opt/0711

# GPU available?
nvidia-smi

# Ports available?
netstat -tulpn | grep -E '(3000|8080|8090|8001)'
```

---

## Performance Tuning

### Ingestion Performance

```bash
# Increase concurrent extractions
MAX_CONCURRENT_EXTRACTIONS=20

# Larger embedding batch size
BATCH_SIZE=64

# More Ray workers
docker compose up -d --scale ray-worker=4
```

### Inference Performance

```bash
# Use multiple GPUs
TENSOR_PARALLEL_SIZE=2

# Increase batch size
MAX_NUM_SEQS=512

# Enable continuous batching
docker compose restart vllm
```

### Memory Optimization

```bash
# Reduce vLLM context length
MAX_MODEL_LEN=8192

# Limit embedding model batch size
BATCH_SIZE=16

# Add swap if needed
sudo fallocate -l 32G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## Security

### Network Security

By default, all services run on localhost. For remote access:

1. **Use reverse proxy** (nginx, Caddy)
2. **Enable HTTPS** with valid certificates
3. **Implement authentication** at proxy level
4. **Firewall rules** to restrict access

Example nginx config:
```nginx
server {
    listen 443 ssl http2;
    server_name ai.yourcompany.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/ {
        proxy_pass http://localhost:8080/api/;
    }

    location /ws {
        proxy_pass http://localhost:8080/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Data Protection

- **Encryption at rest**: Consider encrypting `/opt/0711/data` volume
- **Access control**: Use file system permissions
- **Audit logs**: All queries logged to lakehouse
- **GDPR compliance**: Customer data stays on customer infrastructure

### API Key Management

**Never commit `.env` file!**

```bash
# Generate strong secrets
openssl rand -hex 32 > jwt_secret.txt
openssl rand -hex 16 > minio_secret.txt

# Set in .env
JWT_SECRET=$(cat jwt_secret.txt)
MINIO_SECRET_KEY=$(cat minio_secret.txt)

# Secure the files
chmod 600 .env
rm jwt_secret.txt minio_secret.txt
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     0711 PLATFORM                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   │
│  │  INGESTION   │──▶│  LAKEHOUSE   │──▶│     MCPs     │   │
│  │              │   │              │   │              │   │
│  │ • Crawlers   │   │ • Delta Lake │   │ • CTAX       │   │
│  │ • Handlers   │   │ • Lance DB   │   │ • LAW        │   │
│  │ • Claude AI  │   │ • Embeddings │   │ • ETIM       │   │
│  └──────────────┘   └──────────────┘   │ • HR         │   │
│                                         │ • General    │   │
│                                         └──────────────┘   │
│                              ▲                             │
│                              │                             │
│                     ┌────────┴────────┐                    │
│                     │   CONSOLE UI    │                    │
│                     │  (Chat, Admin)  │                    │
│                     └─────────────────┘                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Support

- **Documentation**: https://docs.0711.ai
- **Issues**: https://github.com/0711/platform/issues
- **Email**: support@0711.ai

---

**Built with ❤️ for German Mittelstand**
