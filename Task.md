# Task: Deploy & Test 0711-OS Platform

**Priority:** High  
**Assigned:** Claude Code (H200)  
**Status:** Ready for Testing
**Updated:** 2026-01-30 (Session 2)

---

## 🚀 MAJOR UPDATES PUSHED TODAY

### 1. Product Intelligence System
Auto-analyzes uploaded products and recommends connectors:
- Field detection (any naming convention)
- Category detection (electrical, automotive, industrial)
- Completeness analysis
- Connector auto-enable logic

### 2. Smart Onboarding Frontend
Zero-config "dump your data, we figure it out":
- `/onboarding` - Upload → Analyze → Deploy → Chat

### 3. New Frontend Pages
- `/connectors` - Docker-style connector catalog
- `/models` - AI models hub (pull like Docker)
- `/experts` - Expert marketplace
- `/experts/[id]` - Expert booking flow
- `/bookings` - My bookings

### 4. Focused Connector Catalog
18 business-critical connectors:
- TENDER, WETTBEWERB, PRICE MONITOR
- AMAZON, SHOPIFY, IDEALO, GOOGLE SHOPPING
- DATANORM, BMECAT, PUBLISH
- ETIM, ECLASS

---

## ✅ TASK 1: Pull Latest & Run Migrations

```bash
cd ~/OS
git pull origin main

# Check what's new
git log --oneline -10

# Activate venv or use Docker
source venv/bin/activate

# Run migrations
alembic upgrade head

# Seed the NEW focused connector catalog
python scripts/seed_connectors_focused.py
```

---

## ✅ TASK 2: Test Product Intelligence API

```bash
# Test the demo endpoint
curl http://localhost:4080/api/product-intelligence/quick-analysis | jq '.report | {category: .primary_category, quality: .completeness_score, connectors: .auto_enabled_connectors}'

# Expected output:
# {
#   "category": "electrical",
#   "quality": 78.5,
#   "connectors": ["etim", "publish", "datanorm"]
# }
```

---

## ✅ TASK 3: Test Smart Onboarding API

```bash
# Test with demo data
curl -X POST http://localhost:4080/api/smart-onboarding/demo/analyze | jq '.report | {products: .metrics.total_products, model: .business_model.type, value: .value}'

# Expected output:
# {
#   "products": 125000,
#   "model": "B2B Distributor",
#   "value": { "revenue_opportunity": "€12.5M", ... }
# }
```

---

## ✅ TASK 4: Test Connector Catalog API

```bash
# Get categories
curl http://localhost:4080/api/connectors/categories | jq '.categories[] | {name: .display_name, count: .connector_count}'

# Get featured connectors
curl http://localhost:4080/api/connectors/featured | jq '.connectors[] | {name: .display_name, price: .price_per_month_cents}'

# Search for tender connectors
curl "http://localhost:4080/api/connectors?category=tenders" | jq '.connectors[] | .display_name'
```

---

## ✅ TASK 5: Frontend Build Test

```bash
cd console/frontend

# Install dependencies (if needed)
npm install

# Build
npm run build

# If build succeeds, start
npm run dev
```

Then check these pages work:
- http://localhost:3000/connectors
- http://localhost:3000/models
- http://localhost:3000/experts
- http://localhost:3000/onboarding

---

## ✅ TASK 6: Full Docker Deployment

```bash
# Build all containers
docker compose build

# Start infrastructure
docker compose up -d postgres redis minio

# Wait, then run migrations
sleep 10
docker compose run --rm api alembic upgrade head
docker compose run --rm api python scripts/seed_connectors_focused.py

# Start AI services
docker compose up -d vllm embeddings

# Wait for vLLM to load model (check logs)
docker compose logs -f vllm

# Once ready, start full stack
docker compose up -d
```

---

## 📊 Report Back

Update this section after testing:

```yaml
Status: [ ] Pending / [ ] Testing / [ ] Complete / [ ] Issues

Git Pull:
  - Latest commit: 
  - Files changed: 

Migrations:
  - Status: 
  - Tables created: 

Connector Seed:
  - Categories: 
  - Connectors: 

API Tests:
  product-intelligence: [ ] Pass / [ ] Fail
  smart-onboarding: [ ] Pass / [ ] Fail
  connectors: [ ] Pass / [ ] Fail

Frontend Build:
  - Status: 
  - Errors: 

Docker:
  - Containers running: 
  - GPU utilization: 
  - vLLM model loaded: 

Notes:
```

---

## 🔗 Expected Endpoints After Deploy

| Endpoint | Test |
|----------|------|
| `/api/connectors` | `curl localhost:4080/api/connectors` |
| `/api/connectors/categories` | `curl localhost:4080/api/connectors/categories` |
| `/api/product-intelligence/quick-analysis` | `curl -X POST localhost:4080/api/product-intelligence/quick-analysis` |
| `/api/smart-onboarding/demo/analyze` | `curl -X POST localhost:4080/api/smart-onboarding/demo/analyze` |
| `/health` | `curl localhost:4080/health` |

---

## 🐛 Known Issues to Watch

1. **react-dropzone** - Make sure `npm install` runs in frontend
2. **ConnectorCategory model** - If table doesn't exist, seed will fail
3. **Anthropic API key** - Product Intelligence works better with Claude

---

## Files Changed Today

```
NEW:
├── api/services/product_intelligence_service.py (34KB)
├── api/services/intelligent_onboarding_service.py (30KB)
├── api/routes/product_intelligence.py
├── api/routes/intelligent_onboarding.py
├── scripts/seed_connectors_focused.py
├── docs/PRODUCT_INTELLIGENCE_FLOW.md
├── docs/INTELLIGENT_ONBOARDING.md
└── console/frontend/src/app/
    ├── connectors/page.tsx
    ├── models/page.tsx
    ├── experts/page.tsx
    ├── experts/[id]/page.tsx
    ├── bookings/page.tsx
    └── onboarding/page.tsx
```
