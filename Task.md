# Task: Complete H200 Deployment with Local Models

**Priority:** High  
**Assigned:** Claude Code (H200)  
**Status:** Continue Deployment
**Updated:** 2026-01-30

---

## 🎯 IMMEDIATE ACTION

Die H200 hat bereits lokale Modelle! Nutze diese statt API.

### Step 1: Check Available Local Models

```bash
# Check what models are already downloaded
ls -la ~/.cache/huggingface/hub/ 2>/dev/null || echo "No HF cache"
ls -la /models/ 2>/dev/null || echo "No /models dir"
ls -la ~/models/ 2>/dev/null || echo "No ~/models dir"

# Check if Ollama is installed and what models it has
ollama list 2>/dev/null || echo "Ollama not installed"

# Check for vLLM or other model servers already running
docker ps | grep -E "vllm|ollama|llama|mistral|qwen"
ps aux | grep -E "vllm|ollama|llama"

# Check GPU memory usage (see if model is already loaded)
nvidia-smi
```

**Report back which models you find!**

### Step 2: Add HuggingFace Token (for any gated models)

```bash
cd ~/OS

cat >> .env << 'EOF'

# HuggingFace Token (provided by user)
HF_TOKEN=<USE_TOKEN_FROM_CHAT>
EOF

echo "✓ HF token added"
```

### Step 3: Configure for Local Model

Based on what's available, choose ONE:

**Option A: If Qwen 2.5 72B is available:**
```bash
cat >> .env << 'EOF'
VLLM_MODEL=Qwen/Qwen2.5-72B-Instruct
LLM_PROVIDER=vllm
LLM_URL=http://localhost:7005
EOF
```

**Option B: If Mistral Large is available locally:**
```bash
cat >> .env << 'EOF'
VLLM_MODEL=mistralai/Mistral-Large-Instruct-2407
LLM_PROVIDER=vllm
LLM_URL=http://localhost:7005
EOF
```

**Option C: If using Ollama:**
```bash
cat >> .env << 'EOF'
LLM_PROVIDER=ollama
LLM_MODEL=qwen2.5:72b
OLLAMA_URL=http://localhost:11434
EOF
```

**Option D: If there's already a model server running:**
```bash
# Find which port it's on
netstat -tlnp | grep -E "8000|8080|11434"

# Then configure:
cat >> .env << 'EOF'
LLM_PROVIDER=vllm  # or ollama
LLM_URL=http://localhost:<PORT>
EOF
```

### Step 4: Deploy vLLM (if not already running)

```bash
# Only if vLLM is NOT already running:
docker compose -f docker-compose.h200.yml up -d vllm

# Monitor startup (takes a few minutes to load model)
docker compose -f docker-compose.h200.yml logs -f vllm

# Wait for "Application startup complete"
```

### Step 5: Deploy Application Services

```bash
# Deploy app services
docker compose -f docker-compose.h200.yml up -d api console-backend console-frontend website

# Check all services
docker compose -f docker-compose.h200.yml ps

# Health checks
curl http://localhost:4080/health
curl http://localhost:4010/health
curl http://localhost:4020
```

### Step 6: Run Migrations & Seed

```bash
# Migrations
docker compose -f docker-compose.h200.yml exec api alembic upgrade head

# Seed connectors (18 business connectors)
docker compose -f docker-compose.h200.yml exec api python scripts/seed_connectors_focused.py
```

### Step 7: Test Everything

```bash
# Test connector catalog
curl http://localhost:4080/api/connectors/categories | jq '.categories[] | .display_name'

# Test product intelligence
curl -X POST http://localhost:4080/api/product-intelligence/quick-analysis | jq '.report | {category: .primary_category, connectors: .auto_enabled_connectors}'

# Test chat with local model (if API supports it)
curl -X POST http://localhost:4080/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Was ist ETIM?"}' | jq '.response'
```

---

## 📊 What Models to Look For

| Model | Size | Good For |
|-------|------|----------|
| **Qwen 2.5 72B** | ~140GB | Best overall, great German |
| **Qwen 2.5 32B** | ~65GB | Fast, still very good |
| **Mistral Large** | ~130GB | Excellent reasoning |
| **Llama 3.3 70B** | ~140GB | Good tool use |
| **Mixtral 8x22B** | ~90GB | Fast MoE model |

The H200 has **80GB VRAM** - can easily run any 70B model!

---

## 📋 Report Back

Tell me:

```yaml
Available Models Found:
  HF Cache:
  /models:
  Ollama:
  Already Running:

GPU Status:
  nvidia-smi output:
  VRAM used:
  VRAM free:

Model Server:
  Type: [vllm/ollama/other]
  Port:
  Model loaded:

Deployment Status:
  api:
  console-backend:
  console-frontend:
  website:

Tests:
  /health:
  /api/connectors:
  chat test:
```

---

## 🔑 API Keys Added

```yaml
HuggingFace: ✅ (provided in chat - add to .env)
Mistral API: ✅ (backup if needed)
Anthropic: ❓ (add if available)
```
