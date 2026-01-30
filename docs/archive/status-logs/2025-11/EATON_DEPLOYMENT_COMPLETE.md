# EATON Deployment - Shared MCP Architecture Implementation

**Date**: 2025-11-30
**Status**: ✅ Code Complete - Ready for Testing

---

## 🎯 Implementation Summary

Successfully implemented a **shared MCP services architecture** where customers access shared MCP services (like ETIM) without per-customer deployments, resulting in:

- **Faster deployments**: 3 containers instead of 7+ per customer
- **Lower resource usage**: One ETIM MCP serves all customers
- **Easier updates**: Update ETIM MCP once, all customers benefit
- **Flexible activation**: Customers enable/disable MCPs without redeployment
- **Better isolation model**: Data isolation at query level via customer_id context

---

## ✅ What Was Completed

### 1. MCP Router (`orchestrator/mcp/mcp_router.py`)
- **Purpose**: Routes customer queries to shared MCP services
- **Features**:
  - Customer context injection (customer_id, lakehouse_path)
  - MCP registry with capabilities and versions
  - Health checking for MCP services
  - Support for multiple shared MCPs (currently ETIM at port 7779)

### 2. Deployment Orchestrator Updates
**File**: `provisioning/api/services/deployment_orchestrator.py`
- **Removed**: Per-customer MCP container deployment
- **Removed**: LoRA trainer container (deferred)
- **Updated**: Documentation to reflect shared MCP model

### 3. EATON Docker Compose (3 Containers Only)
**File**: `/home/christoph.bertsch/0711/deployments/eaton/docker-compose.yml`

**Containers**:
1. **eaton-vllm** (port 9300)
   - Mixtral 8x7B-Instruct
   - GPU: CUDA device 1, 40% memory utilization
   - LoRA enabled (rank 64)
   - Configured with external MCP URL

2. **eaton-embeddings** (port 9301)
   - multilingual-e5-large model
   - Customer-specific embedding service

3. **eaton-lakehouse**
   - Mounts `/tmp/lakehouse/eaton/` with existing data:
     - 21 documents
     - 31,807 vector embeddings (160MB)
     - Delta Lake tables (general_documents, general_chunks)

### 4. Customer Model Updates
**File**: `api/models/customer.py`
- **Added**: `enabled_mcps` JSONB field
- **Example**: `{"etim": true, "ctax": false, "law": false}`
- **Migration**: `migrations/versions/20251130_092000_add_enabled_mcps_to_customer.py`

### 5. MCP Services API
**File**: `api/routes/mcp_services.py`

**Endpoints**:
- `GET /api/mcp-services/available` - List all shared MCPs with pricing
- `GET /api/mcp-services/enabled` - List MCPs enabled for customer
- `POST /api/mcp-services/enable/{mcp_name}` - Enable MCP (no deployment)
- `POST /api/mcp-services/disable/{mcp_name}` - Disable MCP access
- `GET /api/mcp-services/{mcp_name}/info` - Get MCP details
- `POST /api/mcp-services/query` - Query MCP with customer context
- `GET /api/mcp-services/{mcp_name}/health` - Check MCP health

---

## 📊 EATON Data Ingestion Status

### Already Ingested ✅
- **Documents**: 21 files (96 MB)
  - XLSX (6), PDF (6), XML (5), ZIP (2), CSV (1), XLSM (1)
- **Chunks**: 31,807 text chunks
  - 33M characters, 3.5M words
  - Average: 1,046 chars, 112 words per chunk
- **Embeddings**: 31,807 vectors (1024-dim, 160MB in LanceDB)
- **Location**: `/tmp/lakehouse/eaton/`

### Sample Files
- ECLASS 13 Examples.xml
- PDH Extract.xlsx
- ETIM BMEcat Guideline V5-0.pdf
- ETIM xChange Guideline V1.0.pdf
- Product catalog spreadsheets

---

## 🚀 Next Steps: Deployment & Testing

### Step 1: Run Database Migration
```bash
cd /home/christoph.bertsch/0711/0711-OS
alembic upgrade head
```

### Step 2: Enable ETIM MCP for EATON
```sql
-- Connect to PostgreSQL
psql postgresql://0711:0711_dev_password@localhost:4005/0711_control

-- Enable ETIM MCP for EATON
UPDATE customers
SET enabled_mcps = '{"etim": true}'::jsonb
WHERE company_name = 'Eaton Industries GmbH';

-- Verify
SELECT id, company_name, enabled_mcps FROM customers WHERE company_name LIKE '%Eaton%';
```

### Step 3: Verify ETIM MCP is Running
```bash
# Check ETIM MCP containers
docker ps | grep etim

# Should see:
# etim-eclass-mcp
# etim-postgres
# enrichment-mcp
# quality-assurance-mcp
# etim-llm-service (optional)

# Test ETIM MCP health
curl http://localhost:7779/health
```

### Step 4: Deploy EATON Stack
```bash
cd /home/christoph.bertsch/0711/deployments/eaton
docker compose up -d

# Watch vLLM model loading (takes 2-5 minutes)
docker logs eaton-vllm -f

# Verify all 3 containers running
docker ps --filter "name=eaton"

# Should see:
# eaton-vllm (port 9300)
# eaton-embeddings (port 9301)
# eaton-lakehouse
```

### Step 5: Test EATON Stack

**Test 1: vLLM Health**
```bash
curl http://localhost:9300/v1/models
```

**Test 2: Embeddings Service**
```bash
curl -X POST http://localhost:9301/embed \
  -H "Content-Type: application/json" \
  -d '{"texts": ["test product classification"]}'
```

**Test 3: Lakehouse Access (check if data is accessible)**
```bash
docker exec eaton-lakehouse ls -la /data/lakehouse/lance/
docker exec eaton-lakehouse ls -la /data/lakehouse/delta/
```

### Step 6: Test ETIM MCP Integration

**Test 1: ETIM MCP Availability**
```bash
curl http://localhost:4080/api/mcp-services/available
```

**Test 2: Check EATON's Enabled MCPs**
```bash
# Get JWT token first
TOKEN=$(curl -X POST http://localhost:4080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "michael.weber@eaton.com", "password": "test"}' \
  | jq -r '.token')

curl http://localhost:4080/api/mcp-services/enabled \
  -H "Authorization: Bearer $TOKEN"

# Should return: {"enabled_mcps": ["etim"]}
```

**Test 3: Query ETIM MCP with EATON Context**
```bash
curl -X POST http://localhost:4080/api/mcp-services/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mcp_name": "etim",
    "query": "Find ECLASS products in EATON catalog",
    "context": {}
  }'
```

**Test 4: Direct ETIM MCP Query**
```bash
curl -X POST http://localhost:7779/etim/query \
  -H "X-Customer-ID: eaton" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Classify products from EATON catalog",
    "customer_id": "eaton",
    "context": {
      "lakehouse_path": "/tmp/lakehouse/eaton"
    }
  }'
```

### Step 7: Test RAG Query (vLLM + EATON Data)
```bash
curl -X POST http://localhost:9300/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
    "prompt": "Summarize the products in the EATON catalog",
    "max_tokens": 200,
    "temperature": 0.7
  }'
```

---

## 📁 Files Created/Modified

### New Files (4):
1. ✅ `orchestrator/mcp/mcp_router.py` - MCP routing system
2. ✅ `api/routes/mcp_services.py` - MCP marketplace API
3. ✅ `migrations/versions/20251130_092000_add_enabled_mcps_to_customer.py` - DB migration
4. ✅ `EATON_DEPLOYMENT_COMPLETE.md` - This documentation

### Modified Files (3):
1. ✅ `provisioning/api/services/deployment_orchestrator.py` - Removed MCP containers
2. ✅ `/home/christoph.bertsch/0711/deployments/eaton/docker-compose.yml` - 3 containers only
3. ✅ `api/models/customer.py` - Added enabled_mcps field

---

## 🎯 Success Criteria

- [ ] Database migration runs successfully
- [ ] EATON customer has `enabled_mcps = {"etim": true}`
- [ ] ETIM MCP responds to health checks (port 7779)
- [ ] 3 EATON containers running (vllm, embeddings, lakehouse)
- [ ] vLLM loads Mixtral model successfully
- [ ] ETIM MCP can query EATON's 31K vectors
- [ ] API returns ETIM as available and enabled for EATON
- [ ] MCP query returns results from EATON data

---

## 🏗️ Architecture Diagram

```
EATON Deployment (3 containers)
├── eaton-vllm (port 9300)
│   └── Mixtral 8x7B with EATON LoRA
├── eaton-embeddings (port 9301)
│   └── multilingual-e5-large
└── eaton-lakehouse
    └── /tmp/lakehouse/eaton/
        ├── lance/embeddings.lance (31,807 vectors)
        └── delta/general_documents, general_chunks

Shared ETIM MCP (not deployed per-customer)
├── etim-eclass-mcp (port 7779)
├── etim-postgres
├── enrichment-mcp
└── quality-assurance-mcp

Integration
└── MCP Router (orchestrator/mcp/mcp_router.py)
    └── Routes EATON queries → ETIM MCP with customer context
```

---

## 💡 Key Benefits

### Before (Per-Customer MCPs):
- 7+ containers per customer
- Duplicate ETIM installations
- Complex updates (update each customer)
- High resource usage

### After (Shared MCPs):
- 3 containers per customer
- One ETIM MCP for all
- Update once, everyone benefits
- 60% fewer containers

---

## 🐛 Troubleshooting

### If vLLM fails to start:
```bash
# Check GPU availability
nvidia-smi

# Check GPU assignment in docker-compose
# CUDA_VISIBLE_DEVICES: '1' should match available GPU
```

### If ETIM MCP not accessible:
```bash
# Check ETIM MCP is running
docker ps | grep etim-eclass-mcp

# Check ETIM MCP logs
docker logs etim-eclass-mcp

# Restart ETIM MCP stack
cd /home/christoph.bertsch/0711/0711-etim-mcp
docker compose restart
```

### If lakehouse data not accessible:
```bash
# Verify mount point
docker inspect eaton-lakehouse | grep -A 10 Mounts

# Should show: /tmp/lakehouse/eaton → /data/lakehouse
```

---

## 📚 Related Documentation

- **ETIM MCP System**: `/home/christoph.bertsch/0711/0711-etim-mcp/README.md`
- **0711-OS Architecture**: `CLAUDE.md`
- **Deployment Flow**: `DEPLOYMENT_FLOW.md`
- **Data Ingestion**: Covered in `CLAUDE.md` (File Upload & Data Ingestion section)

---

**Ready for deployment testing!**
