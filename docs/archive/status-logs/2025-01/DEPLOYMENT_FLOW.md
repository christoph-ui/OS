# 0711 Platform - Complete Deployment Flow

**Per-Customer AI Brain with Continuous Learning**

---

## 🎯 What Happens When EATON Uploads Their First File

### Step-by-Step Automated Deployment

```
1. EATON visits http://localhost:4000/onboarding
   ├─ Enters company info: "Eaton Industries GmbH"
   ├─ Uploads files/folders (products, contracts, etc.)
   └─ Selects MCPs (ETIM, Product Management, CTAX)

2. First file hits upload button
   ├─ Frontend POST → http://localhost:4080/api/upload/files?customer_id=eaton-industries-gmbh
   ├─ Backend receives files
   └─ Stores in MinIO bucket: customer-eaton-industries-gmbh/

3. System detects: First upload! 🚀
   ├─ Creates MinIO bucket (didn't exist before)
   ├─ Triggers deployment orchestrator
   └─ Alert shown: "First upload! Your AI brain is being deployed..."

4. Deployment Orchestrator Executes:

   4a. Port Allocation (Hash-based)
       ├─ vLLM/Mixtral: 5100
       ├─ Embeddings: 5101
       ├─ Console UI: 5110
       ├─ MCP ETIM: 5122
       ├─ MCP Product: 5123
       ├─ MCP CTAX: 5120
       └─ LoRA Trainer: 5130

   4b. Generate docker-compose.yml
       ├─ File: /home/christoph.bertsch/0711/deployments/eaton-industries-gmbh/docker-compose.yml
       ├─ Services: vllm, embeddings, lakehouse, mcp-etim, mcp-product, mcp-ctax, lora-trainer
       └─ Network: eaton-industries-gmbh-network

   4c. Start Docker Services
       ├─ docker compose up -d
       ├─ Pull vLLM image (~15GB)
       ├─ Download Mixtral-8x7B (~48GB)
       ├─ Start all services
       └─ Wait for health checks

5. Initialize Lakehouse
   ├─ Create: /home/christoph.bertsch/0711/data/lakehouse/eaton-industries-gmbh/
   ├─ Delta Lake tables
   ├─ Lance vector indices
   └─ Metadata files

6. Trigger Ingestion Pipeline
   ├─ Read files from MinIO: customer-eaton-industries-gmbh
   ├─ Extract content (PDF, Excel, CSV, etc.)
   ├─ Claude Sonnet 4.5 generates handlers for unknown formats
   ├─ Classify documents to MCPs
   ├─ Chunk text intelligently
   ├─ Generate embeddings (multilingual-e5-large)
   ├─ Load to lakehouse (Delta + Lance)
   └─ Status: "24,385 documents processed"

7. Train Initial LoRA
   ├─ Collect training data from lakehouse
   ├─ Customer domain knowledge
   ├─ Industry terminology
   ├─ Document patterns
   ├─ Train LoRA adapter (1-2 hours)
   ├─ Save: /home/christoph.bertsch/0711/data/loras/eaton-industries-gmbh/v1_20251125/
   └─ Deploy to Mixtral instance

8. MCPs Connect to Data
   ├─ ETIM MCP (5122) → EATON lakehouse
   ├─ Product MCP (5123) → EATON lakehouse
   ├─ CTAX MCP (5120) → EATON lakehouse
   └─ All queries scoped to EATON data only

9. Mark Deployment Active
   ├─ Database: deployment.status = "active"
   ├─ EATON console ready: http://localhost:5110
   └─ EATON can start chatting!

10. User Sees Completion Screen
    ├─ "You're live! 24,385 records indexed"
    ├─ "7 MCPs active"
    ├─ "Click to open console" → http://localhost:5110
    └─ EATON's AI brain is ready!
```

---

## 🔄 Continuous Learning Loop

### Daily (Automated)

```
Every 24 hours:
├─ Collect new interactions from logs
├─ Query-answer pairs
├─ User feedback
├─ MCP outputs
├─ Train incremental LoRA (v2, v3, v4...)
├─ Deploy new version
└─ Mixtral gets smarter at EATON's business

After 30 days:
└─ EATON's Mixtral knows EATON better than any consultant
```

---

## 📂 File Storage Structure

```
MinIO (Port 4050)
├── customer-eaton-industries-gmbh/
│   ├── 20251125_183000_product_catalog.csv
│   ├── 20251125_183001_technical_specs.pdf
│   ├── 20251125_183002_contracts/
│   └── ... (all uploaded files)
│
├── customer-e-procat-gmbh/
│   └── ... (e-ProCat files)
│
└── uploads/  (temporary, general)

Lakehouse
├── eaton-industries-gmbh/
│   ├── delta/  (structured tables)
│   ├── lance/  (vector embeddings)
│   └── graph/  (entity relationships)
│
└── e-procat-gmbh/
    └── ...

LoRAs
├── eaton-industries-gmbh/
│   ├── v1_20251125/  (initial training)
│   ├── v2_20251126/  (after day 1)
│   └── v3_20251127/  (after day 2)
│
└── e-procat-gmbh/
    └── ...

Docker Deployments
├── eaton-industries-gmbh/
│   ├── docker-compose.yml
│   └── .env
│
└── e-procat-gmbh/
    └── ...
```

---

## 🌐 Customer Access Points

### EATON
- **Console**: http://localhost:5110 (or https://eaton.0711.cloud in production)
- **API**: http://localhost:5100 (vLLM)
- **MCPs**: Ports 5120-5129

### e-ProCat
- **Console**: http://localhost:5210
- **API**: http://localhost:5200 (vLLM)
- **MCPs**: Ports 5220-5229

**Complete isolation** - EATON can never see e-ProCat data!

---

## 🎨 Two Deployment Options

### Option 1: Managed (SaaS) - DEFAULT
**Customer perspective:**
1. Go to 0711.cloud/onboarding
2. Upload data
3. Wait 10 minutes
4. Access eaton.0711.cloud
5. You handle all infrastructure

**Your infrastructure:**
- Multiple customer stacks on your servers
- Shared hardware, logical isolation
- You manage updates, backups, scaling

### Option 2: Self-Hosted (On-Premise)
**Customer perspective:**
1. Download install-0711.sh
2. Run on their servers: `sudo ./install-0711.sh --license=ENTERPRISE-EATON-2025`
3. Select data folders
4. Wait 15 minutes
5. Access http://eaton-internal-server

**Their infrastructure:**
- Complete stack on their hardware
- Air-gapped if needed
- Full data sovereignty
- They manage everything

**Installer includes:**
- Docker images bundled
- License validator
- Setup wizard
- Health monitoring
- Auto-update (optional)

---

## 💡 Key Innovations

### 1. Claude-Powered Adaptive Import
```python
EATON uploads proprietary .SAP file
    ↓
Claude Sonnet 4.5 analyzes structure
    ↓
Generates Python handler in 30 seconds
    ↓
Validates & tests
    ↓
Registers for future .SAP files
    ↓
EATON never waits for "developer to build integration"
```

### 2. Per-Customer AI Brain
```
Month 0: Generic Mixtral + EATON data
Month 1: v30 LoRA trained - knows EATON products
Month 3: v90 LoRA - understands EATON processes
Month 6: v180 LoRA - predicts EATON needs
Month 12: EATON's AI is irreplaceable
```

### 3. Full RAG Stack
```
Query: "Show products with EMC compliance issues"
    ↓
Hybrid Search:
├─ Vector: Semantic similarity (Lance)
├─ Structured: SQL on metadata (Delta)
├─ Graph: Product→Cert→Issue (Neo4j)
└─ Combined results

Mixtral + EATON LoRA generates answer
```

---

## 🚀 Current Status

### ✅ COMPLETE
1. File upload → MinIO (working)
2. First upload triggers deployment (working)
3. Per-customer orchestrator (built)
4. Port allocation system (built)
5. Docker-compose generator (built)
6. LoRA training pipeline (built)
7. Ingestion trigger (integrated)
8. Complete RAG stack (Delta + Lance)
9. Claude handler generator (working)

### ⚠️ NEEDS DOCKER IMAGES
- vLLM image (available publicly)
- 0711/platform image (need to build)
- MCP images (need to build)
- LoRA trainer image (need to build)

### ⚠️ NEEDS GPU
- vLLM requires NVIDIA GPU
- Currently configured but not started
- Can start with: `docker compose --profile gpu up vllm`

---

## 🎬 Demo Flow (Ready to Test)

**Right now you can:**

1. Go to http://localhost:4000/onboarding
2. Enter "Eaton Industries GmbH" as company
3. Upload sample files
4. Watch backend logs:
   ```bash
   tail -f /tmp/0711_api.log
   ```
5. See:
   - ✓ Files uploaded to MinIO
   - ✓ Bucket created: customer-eaton-industries-gmbh
   - ✓ Deployment triggered
   - ✓ docker-compose.yml generated
   - ✓ Services starting...

**What happens (with GPU):**
- Mixtral downloads & starts (takes ~5 min first time)
- Ingestion processes files
- LoRA trains on EATON data
- Console becomes available at http://localhost:5110

**Without GPU (current):**
- Everything works except AI inference
- Files stored, ingestion ready
- Can add GPU later

---

## 📋 Next Steps

1. **Add GPU** to test full deployment
2. **Build Docker images** for 0711/platform, MCPs
3. **Add deployment mode** choice in onboarding UI
4. **Create self-hosted installer**
5. **Test complete EATON flow** end-to-end

---

**Status**: Complete architecture implemented, ready for GPU deployment! 🚀
