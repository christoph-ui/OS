# Task: Deploy 0711-OS Platform on H200

**Priority:** High  
**Assigned:** Claude Code (H200)  
**Status:** Pending

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

## Step 3: Create Docker Compose for H200

Create `docker-compose.h200.yml`:

```yaml
version: '3.8'

services:
  # =========================================================================
  # Infrastructure
  # =========================================================================
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: os711
      POSTGRES_PASSWORD: os711secret
      POSTGRES_DB: os711
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U os711"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: 0711admin
      MINIO_ROOT_PASSWORD: 0711secret
    volumes:
      - minio_data:/data
    ports:
      - "9000:9000"
      - "9001:9001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3

  # =========================================================================
  # AI Services (GPU)
  # =========================================================================
  vllm:
    image: vllm/vllm-openai:latest
    command: >
      --model Qwen/Qwen2.5-72B-Instruct
      --tensor-parallel-size 1
      --max-model-len 32768
      --gpu-memory-utilization 0.90
      --enable-lora
      --max-lora-rank 64
      --trust-remote-code
    environment:
      HUGGING_FACE_HUB_TOKEN: ${HF_TOKEN}
    ports:
      - "8000:8000"
    volumes:
      - models_cache:/root/.cache/huggingface
      - ./loras:/loras
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped

  embeddings:
    build:
      context: .
      dockerfile: docker/Dockerfile.embeddings
    environment:
      EMBEDDING_MODEL: intfloat/multilingual-e5-large
      EMBEDDING_PORT: "8001"
    ports:
      - "8001:8001"
    volumes:
      - models_cache:/root/.cache/huggingface
    deploy:
      resources:
        limits:
          memory: 8G
    restart: unless-stopped

  # =========================================================================
  # 0711-OS Application
  # =========================================================================
  api:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql://os711:os711secret@postgres:5432/os711
      REDIS_URL: redis://redis:6379
      MINIO_ENDPOINT: minio:9000
      MINIO_ACCESS_KEY: 0711admin
      MINIO_SECRET_KEY: 0711secret
      VLLM_URL: http://vllm:8000
      EMBEDDINGS_URL: http://embeddings:8001
      JWT_SECRET: ${JWT_SECRET:-change-this-in-production}
      DEBUG: "true"
    ports:
      - "4080:4080"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  console-backend:
    build:
      context: ./console
      dockerfile: Dockerfile
    command: ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "4010"]
    environment:
      API_URL: http://api:4080
      VLLM_URL: http://vllm:8000
      DATABASE_URL: postgresql://os711:os711secret@postgres:5432/os711
      REDIS_URL: redis://redis:6379
    ports:
      - "4010:4010"
    depends_on:
      - api
    restart: unless-stopped

  console-frontend:
    build:
      context: ./console/frontend
      dockerfile: Dockerfile
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:4010
      NEXT_PUBLIC_WS_URL: ws://localhost:4010
    ports:
      - "4020:3000"
    depends_on:
      - console-backend
    restart: unless-stopped

  website:
    build:
      context: ./apps/website
      dockerfile: Dockerfile
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:4080
    ports:
      - "4000:3000"
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  minio_data:
  models_cache:

networks:
  default:
    name: 0711-network
```

## Step 4: Create Missing Dockerfiles

### `docker/Dockerfile.embeddings`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    sentence-transformers \
    fastapi \
    uvicorn \
    torch --index-url https://download.pytorch.org/whl/cpu

COPY inference/embeddings_server.py .

ENV EMBEDDING_MODEL=intfloat/multilingual-e5-large
ENV EMBEDDING_PORT=8001

EXPOSE 8001

CMD ["python", "embeddings_server.py"]
```

### `console/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY ../core/ ./core/

EXPOSE 4010

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "4010"]
```

### `console/frontend/Dockerfile`

```dockerfile
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000
CMD ["node", "server.js"]
```

### `apps/website/Dockerfile`

```dockerfile
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000
CMD ["node", "server.js"]
```

## Step 5: Build and Deploy

```bash
# Create directories
mkdir -p loras data/lakehouse

# Pull base images
docker pull vllm/vllm-openai:latest
docker pull pgvector/pgvector:pg16
docker pull redis:7-alpine
docker pull minio/minio:latest

# Build application images
docker compose -f docker-compose.h200.yml build

# Start infrastructure first
docker compose -f docker-compose.h200.yml up -d postgres redis minio

# Wait for healthy
sleep 10

# Start AI services (this will download models - takes time!)
docker compose -f docker-compose.h200.yml up -d vllm embeddings

# Wait for models to load (check logs)
docker compose -f docker-compose.h200.yml logs -f vllm

# Once vLLM shows "Application startup complete", start app services
docker compose -f docker-compose.h200.yml up -d api console-backend console-frontend website
```

## Step 6: Verify Deployment

```bash
# Check all containers
docker compose -f docker-compose.h200.yml ps

# Test endpoints
curl http://localhost:4080/health
curl http://localhost:4010/health
curl http://localhost:8000/health
curl http://localhost:8001/health

# Check GPU utilization
nvidia-smi
```

## Step 7: Report Back

Once deployed, update this file with:
- [ ] GPU info (nvidia-smi output)
- [ ] Container status (docker ps)
- [ ] Health check results
- [ ] Any errors encountered
- [ ] Access URLs

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
