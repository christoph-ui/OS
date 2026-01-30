# Task: Get Website Running NOW + vLLM Multi-GPU Setup

**Priority:** URGENT  
**Assigned:** Claude Code (H200)  
**Updated:** 2026-01-30

---

## 🚨 PRIORITY 1: Website JETZT starten!

Der Chef will klicken! Website first, vLLM optimization later.

### Quick Start (5 Minuten)

```bash
cd ~/OS
git pull origin main

# Add API keys to .env (keys provided in chat)
cat >> .env << 'EOF'
HF_TOKEN=<from_chat>
MISTRAL_API_KEY=<from_chat>
LLM_PROVIDER=mistral
LLM_MODEL=mistral-large-latest
EOF

# Start ALL services (use Mistral API for now, vLLM later)
docker compose -f docker-compose.h200.yml up -d

# Run migrations
docker compose -f docker-compose.h200.yml exec api alembic upgrade head

# Seed connectors
docker compose -f docker-compose.h200.yml exec api python scripts/seed_connectors_focused.py

# Check everything is running
docker compose -f docker-compose.h200.yml ps
```

### Access URLs (share with boss!)

```
📱 Console (Chat):     http://<H200_IP>:4020
🌐 Website:            http://<H200_IP>:4000  
📚 API Docs:           http://<H200_IP>:4080/docs
💾 MinIO Console:      http://<H200_IP>:7003
```

### Quick Test

```bash
# Health check
curl http://localhost:4080/health

# Test connector catalog
curl http://localhost:4080/api/connectors | jq '.connectors | length'
# Should return: 18

# Test a page
curl -I http://localhost:4020
# Should return: HTTP 200
```

---

## 🖥️ PRIORITY 2: vLLM Multi-GPU + LoRA Setup

Once website works, set up the proper local inference:

### Hardware Recap
```yaml
CPUs: 128 Cores
RAM: 1.5 TB
GPUs: 2x H200 (280GB VRAM total)
```

### Create vLLM Multi-GPU Config

```bash
# Create vLLM config for 2x H200
cat > docker-compose.vllm.yml << 'EOF'
version: '3.8'

services:
  vllm:
    image: vllm/vllm-openai:latest
    runtime: nvidia
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all  # Use both GPUs
              capabilities: [gpu]
    environment:
      - HF_TOKEN=${HF_TOKEN}
      - VLLM_TENSOR_PARALLEL_SIZE=2  # Split across 2 GPUs
    command: >
      --model Qwen/Qwen2.5-72B-Instruct
      --tensor-parallel-size 2
      --gpu-memory-utilization 0.90
      --max-model-len 32768
      --enable-lora
      --max-loras 100
      --max-lora-rank 64
      --lora-modules customer_adapters=/app/adapters
      --host 0.0.0.0
      --port 8000
    volumes:
      - ./adapters:/app/adapters:ro
      - huggingface_cache:/root/.cache/huggingface
    ports:
      - "7005:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 5
    shm_size: '32gb'  # For tensor parallel communication

volumes:
  huggingface_cache:
EOF

echo "✓ vLLM config created"
```

### Start vLLM with Multi-GPU

```bash
# Start vLLM (will download model ~140GB, takes time)
docker compose -f docker-compose.vllm.yml up -d vllm

# Monitor startup
docker compose -f docker-compose.vllm.yml logs -f vllm

# Wait for: "Application startup complete"
# Model load takes ~10-15 minutes first time
```

### Switch from Mistral API to Local vLLM

```bash
# Once vLLM is ready, update .env
sed -i 's/LLM_PROVIDER=mistral/LLM_PROVIDER=vllm/' .env
sed -i 's|LLM_MODEL=mistral-large-latest|LLM_MODEL=Qwen/Qwen2.5-72B-Instruct|' .env
echo "LLM_URL=http://localhost:7005" >> .env

# Restart API to use local model
docker compose -f docker-compose.h200.yml restart api
```

### Test Local Inference

```bash
# Test vLLM directly
curl http://localhost:7005/v1/models | jq

# Test chat
curl http://localhost:7005/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-72B-Instruct",
    "messages": [{"role": "user", "content": "Was ist ETIM?"}],
    "max_tokens": 200
  }' | jq '.choices[0].message.content'
```

---

## 📊 Report Back

```yaml
# Fill this out:

Website Status:
  Console (4020): [ ] Running / [ ] Error
  Website (4000): [ ] Running / [ ] Error
  API (4080): [ ] Running / [ ] Error

Access URL: http://_______________

Connectors Seeded: [ ] Yes (18) / [ ] No

vLLM Status:
  Multi-GPU: [ ] Running / [ ] Pending
  Model: Qwen 2.5 72B
  GPUs Used: 0 / 2

Can Boss Click Through: [ ] YES! / [ ] Not yet
```

---

## 🎯 Summary

1. **JETZT**: Website starten mit Mistral API (5 min)
2. **DANACH**: vLLM Multi-GPU Setup (30 min)
3. **SPÄTER**: LoRA Training Pipeline

**Boss kann klicken sobald Step 1 fertig ist!**
