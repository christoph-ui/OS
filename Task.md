# Task: Complete H200 Deployment with Mistral Large

**Priority:** High  
**Assigned:** Claude Code (H200)  
**Status:** Continue Deployment
**Updated:** 2026-01-30

---

## 🎯 IMMEDIATE ACTION

Infrastructure is running! Now configure Mistral Large and deploy app services.

### Step 1: Add Mistral API Key

```bash
cd ~/OS

# Add Mistral API key to .env
cat >> .env << 'EOF'

# Mistral AI
MISTRAL_API_KEY=FHvbqUs1rr4X3q97fN1LqzUCj6yjiF3J
LLM_PROVIDER=mistral
LLM_MODEL=mistral-large-latest
EOF

echo "✓ Mistral API key added"
```

### Step 2: Skip vLLM (using Mistral API instead)

We'll use Mistral's hosted API instead of local vLLM. This means:
- No GPU needed for LLM inference
- Faster startup
- Mistral Large 2 is very capable (128K context)

### Step 3: Deploy Application Services

```bash
# Build and start app services
docker compose -f docker-compose.h200.yml up -d api

# Wait for API to be healthy
sleep 10
curl http://localhost:4080/health

# Start frontend services
docker compose -f docker-compose.h200.yml up -d console-backend console-frontend website

# Check all services
docker compose -f docker-compose.h200.yml ps
```

### Step 4: Run Database Migrations

```bash
# Run migrations
docker compose -f docker-compose.h200.yml exec api alembic upgrade head

# Seed connector catalog
docker compose -f docker-compose.h200.yml exec api python scripts/seed_connectors_focused.py
```

### Step 5: Test APIs

```bash
# Health check
curl http://localhost:4080/health | jq

# Test connector catalog
curl http://localhost:4080/api/connectors/categories | jq

# Test product intelligence (demo)
curl -X POST http://localhost:4080/api/product-intelligence/quick-analysis | jq '.report.primary_category'

# Test smart onboarding (demo)
curl -X POST http://localhost:4080/api/smart-onboarding/demo/analyze | jq '.report.summary'
```

---

## 📊 Current Status

### ✅ Running (from previous deployment)
| Service | Port | Status |
|---------|------|--------|
| PostgreSQL | 7000 | ✅ Running |
| Redis | 7001 | ✅ Running |
| MinIO | 7002/7003 | ✅ Running |
| Embeddings | 7004 | ✅ Running |

### 🚀 To Deploy Now
| Service | Port | Status |
|---------|------|--------|
| API | 4080 | 🔄 Deploy |
| Console Backend | 4010 | 🔄 Deploy |
| Console Frontend | 4020 | 🔄 Deploy |
| Website | 4000 | 🔄 Deploy |

### ⏸️ Skipped
| Service | Reason |
|---------|--------|
| vLLM | Using Mistral API instead |

---

## 🔑 API Keys Status

```yaml
Mistral: ✅ FHvb...F3J (just added)
HuggingFace: ⏸️ Not needed (using Mistral API)
Anthropic: ❓ Add if available for better Product Intelligence
```

---

## 📋 Report After Completion

Update this:

```yaml
Deployment Status: [ ] Pending / [ ] Complete / [ ] Issues

Services Running:
  api: 
  console-backend:
  console-frontend:
  website:

Migrations:
  status:
  tables:

Connector Seed:
  categories:
  connectors:

API Tests:
  /health:
  /api/connectors:
  /api/product-intelligence:
  /api/smart-onboarding:

Access URLs:
  API Docs: http://<IP>:4080/docs
  Console: http://<IP>:4020
  Website: http://<IP>:4000

Notes:
```

---

## 🌐 Final Access Points

After deployment completes:

| Service | URL |
|---------|-----|
| **API Docs** | http://IP:4080/docs |
| **Console (Chat)** | http://IP:4020 |
| **Website** | http://IP:4000 |
| **MinIO Console** | http://IP:7003 |

---

## 💡 Note on LLM Provider

The system now supports multiple LLM providers:

```python
# In code, the LLM provider is selected via env:
LLM_PROVIDER=mistral  # or "anthropic", "openai", "vllm"
LLM_MODEL=mistral-large-latest

# For chat completions, the API routes to Mistral
```

If you want to add Anthropic for Product Intelligence (better at German text analysis):
```bash
echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env
```
