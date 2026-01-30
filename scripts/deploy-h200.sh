#!/bin/bash
# =============================================================================
# 0711-OS H200 Deployment Script
# =============================================================================
# 
# Deploys 0711-OS to H200 GPU server with the new decoupled architecture:
# - Playground (shared ingestion cluster)
# - Per-customer clean instances
# - Export/Import data sync
#
# Usage:
#   ./scripts/deploy-h200.sh [--clean] [--playground-only] [--full]
#
# =============================================================================

set -e

# Configuration
H200_HOST="${H200_HOST:-h200.0711.io}"
H200_USER="${H200_USER:-christoph.bertsch}"
DEPLOY_PATH="${DEPLOY_PATH:-/home/christoph.bertsch/0711}"
REPO_URL="https://github.com/christoph-ui/OS.git"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[0711]${NC} $1"; }
success() { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; exit 1; }

# =============================================================================
# Functions
# =============================================================================

check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check SSH access
    if ! ssh -o ConnectTimeout=5 "$H200_USER@$H200_HOST" "echo ok" &>/dev/null; then
        error "Cannot SSH to $H200_HOST. Check SSH config."
    fi
    success "SSH access OK"
    
    # Check GPU
    GPU_INFO=$(ssh "$H200_USER@$H200_HOST" "nvidia-smi --query-gpu=name,memory.total --format=csv,noheader" 2>/dev/null || echo "")
    if [[ -z "$GPU_INFO" ]]; then
        error "No GPU detected on $H200_HOST"
    fi
    success "GPU detected: $GPU_INFO"
    
    # Check Docker
    DOCKER_VERSION=$(ssh "$H200_USER@$H200_HOST" "docker --version" 2>/dev/null || echo "")
    if [[ -z "$DOCKER_VERSION" ]]; then
        error "Docker not installed on $H200_HOST"
    fi
    success "Docker: $DOCKER_VERSION"
}

deploy_code() {
    log "Deploying code to $H200_HOST..."
    
    ssh "$H200_USER@$H200_HOST" bash <<EOF
        set -e
        mkdir -p $DEPLOY_PATH
        cd $DEPLOY_PATH
        
        if [ -d ".git" ]; then
            echo "Updating existing repo..."
            git fetch origin
            git reset --hard origin/main
        else
            echo "Cloning fresh..."
            cd ..
            rm -rf 0711-os 2>/dev/null || true
            git clone $REPO_URL 0711-os
            cd 0711-os
        fi
        
        # Copy .env if exists
        if [ -f ".env.example" ] && [ ! -f ".env" ]; then
            cp .env.example .env
            echo "Created .env from example - EDIT IT!"
        fi
EOF
    
    success "Code deployed"
}

build_images() {
    log "Building Docker images on $H200_HOST..."
    
    ssh "$H200_USER@$H200_HOST" bash <<EOF
        set -e
        cd $DEPLOY_PATH
        
        # Build base images
        echo "Building embeddings service..."
        docker build -t 0711-os-embeddings:latest -f docker/Dockerfile.embeddings .
        
        echo "Building API service..."
        docker build -t 0711-os-api:latest -f Dockerfile .
        
        echo "Building console..."
        docker build -t 0711-os-console:latest -f console/Dockerfile .
        
        # Pull vLLM (pre-built)
        echo "Pulling vLLM image..."
        docker pull vllm/vllm-openai:latest
EOF
    
    success "Images built"
}

deploy_playground() {
    log "Deploying Playground cluster..."
    
    ssh "$H200_USER@$H200_HOST" bash <<EOF
        set -e
        cd $DEPLOY_PATH
        
        # Create playground docker-compose
        cat > docker-compose.playground.yml <<'COMPOSE'
services:
  # =========================================================================
  # Infrastructure
  # =========================================================================
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: os711
      POSTGRES_PASSWORD: \${POSTGRES_PASSWORD:-os711secret}
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

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: \${MINIO_ROOT_USER:-0711admin}
      MINIO_ROOT_PASSWORD: \${MINIO_ROOT_PASSWORD:-0711secret}
    volumes:
      - minio_data:/data
    ports:
      - "4050:9000"   # S3 API
      - "4051:9001"   # Console

  # =========================================================================
  # AI Services (Shared across playground)
  # =========================================================================
  embeddings:
    image: 0711-os-embeddings:latest
    environment:
      EMBEDDING_MODEL: intfloat/multilingual-e5-large
      EMBEDDING_PORT: "8001"
      INFERENCE_EMBEDDING_DEVICE: cpu
    ports:
      - "8001:8001"
    deploy:
      resources:
        limits:
          memory: 8G

  vllm-playground:
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
      HUGGING_FACE_HUB_TOKEN: \${HF_TOKEN}
    ports:
      - "8000:8000"
    volumes:
      - models_cache:/root/.cache/huggingface
      - lora_adapters:/loras
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  # =========================================================================
  # 0711-OS Services
  # =========================================================================
  api:
    image: 0711-os-api:latest
    environment:
      DATABASE_URL: postgresql://os711:\${POSTGRES_PASSWORD:-os711secret}@postgres:5432/os711
      REDIS_URL: redis://redis:6379
      MINIO_ENDPOINT: minio:9000
      MINIO_ACCESS_KEY: \${MINIO_ROOT_USER:-0711admin}
      MINIO_SECRET_KEY: \${MINIO_ROOT_PASSWORD:-0711secret}
      VLLM_URL: http://vllm-playground:8000
      EMBEDDINGS_URL: http://embeddings:8001
    ports:
      - "4080:4080"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started

  console-backend:
    image: 0711-os-console:latest
    command: ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "4010"]
    environment:
      API_URL: http://api:4080
      VLLM_URL: http://vllm-playground:8000
      DATABASE_URL: postgresql://os711:\${POSTGRES_PASSWORD:-os711secret}@postgres:5432/os711
    ports:
      - "4010:4010"
    depends_on:
      - api

  console-frontend:
    image: 0711-os-console:latest
    command: ["npm", "run", "start"]
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:4010
    ports:
      - "4020:4020"
    depends_on:
      - console-backend

volumes:
  postgres_data:
  redis_data:
  minio_data:
  models_cache:

networks:
  default:
    name: 0711-playground
COMPOSE

        # Start playground
        echo "Starting playground cluster..."
        docker compose -f docker-compose.playground.yml up -d
        
        echo "Waiting for services..."
        sleep 30
        
        # Health check
        curl -sf http://localhost:4080/health || echo "API not ready yet"
        curl -sf http://localhost:8001/health || echo "Embeddings not ready yet"
EOF
    
    success "Playground deployed"
}

show_status() {
    log "Checking deployment status..."
    
    ssh "$H200_USER@$H200_HOST" bash <<EOF
        cd $DEPLOY_PATH
        
        echo ""
        echo "=========================================="
        echo "         0711-OS Deployment Status        "
        echo "=========================================="
        echo ""
        
        # Docker containers
        echo "Containers:"
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "0711|vllm|minio|postgres|redis|embeddings" || echo "No containers running"
        
        echo ""
        echo "GPU Status:"
        nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu --format=csv,noheader
        
        echo ""
        echo "Access Points:"
        echo "  Console:    http://$H200_HOST:4020"
        echo "  API:        http://$H200_HOST:4080"
        echo "  API Docs:   http://$H200_HOST:4080/docs"
        echo "  MinIO:      http://$H200_HOST:4051"
        echo "  vLLM:       http://$H200_HOST:8000"
        echo ""
EOF
}

# =============================================================================
# Main
# =============================================================================

main() {
    echo ""
    echo "=========================================="
    echo "     0711-OS H200 Deployment             "
    echo "=========================================="
    echo ""
    
    case "${1:-full}" in
        --check)
            check_prerequisites
            ;;
        --code)
            deploy_code
            ;;
        --build)
            build_images
            ;;
        --playground-only)
            check_prerequisites
            deploy_code
            build_images
            deploy_playground
            show_status
            ;;
        --status)
            show_status
            ;;
        --full|*)
            check_prerequisites
            deploy_code
            build_images
            deploy_playground
            show_status
            ;;
    esac
    
    echo ""
    success "Deployment complete!"
}

main "$@"
