# 0711 Platform - Complete Architecture

**Per-Customer AI Brain with Continuous Learning**

---

## 🧠 Core Concept

Each customer gets their **own dedicated AI brain** that:
- Learns from their specific business
- Understands their data formats
- Improves with every interaction
- Never shares intelligence with other customers

---

## 📐 Per-Customer Stack

### Example: EATON Deployment

```
EATON Installation (Ports 5100-5199)
├── Mixtral-8x7B Instance (Port 5100)
│   ├── Base: Mixtral-8x7B-Instruct (24GB)
│   ├── EATON LoRA v1: Product data specialist (2GB)
│   ├── EATON LoRA v2: German technical docs (2GB)
│   └── Hot-swappable <1 second
│
├── Embeddings (Port 5101)
│   └── multilingual-e5-large (4GB)
│
├── Customer Lakehouse
│   ├── Delta Lake: Structured data tables
│   ├── Lance DB: Vector embeddings
│   ├── Neo4j Graph: Entity relationships
│   └── All isolated to EATON only
│
├── MinIO Bucket: customer-eaton
│   ├── Raw files uploaded
│   ├── Processed documents
│   └── Training data for LoRAs
│
├── Selected MCPs
│   ├── ETIM Classification (Port 5122)
│   ├── Product Management (Port 5123)
│   └── CTAX (Port 5120)
│
├── LoRA Trainer (Port 5130)
│   ├── Trains from EATON interactions
│   ├── Daily updates
│   └── Automatic deployment
│
└── Console UI (Port 5110)
    └── EATON-branded interface
```

### Example: e-ProCat Deployment

```
e-ProCat Installation (Ports 5200-5299)
├── Mixtral-8x7B Instance (Port 5200)
├── Embeddings (Port 5201)
├── Lakehouse (e-ProCat data only)
├── MinIO: customer-eprocat
├── MCPs: CTAX, ETIM, Tender
├── LoRA Trainer (Port 5230)
└── Console UI (Port 5210)
```

**Complete Isolation** - No data sharing between customers!

---

## 🔄 Complete Data Flow

### 1. File Upload → Intelligent Import

```
EATON uploads proprietary .DAT files
    ↓
MinIO: customer-eaton/raw/
    ↓
Claude Sonnet 4.5 analyzes file
    ↓
Generates Python import handler
    ↓
Validates & tests handler
    ↓
Registers handler for future .DAT files
    ↓
Extracts data → Lakehouse
```

**Key Innovation**: Claude auto-generates import scripts for ANY format!

### 2. Data Ingestion → RAG Pipeline

```
Files in MinIO
    ↓
Crawl & Extract (10+ built-in handlers + Claude-generated)
    ↓
Classify to MCPs (CTAX, LAW, ETIM, etc.)
    ↓
Chunk intelligently (structure-aware)
    ↓
Embed with multilingual-e5-large
    ↓
Load to Lakehouse:
    ├── Delta Lake: Structured tables
    ├── Lance: Vector search
    └── Graph: Entity relationships
```

### 3. Query → MCP Orchestration

```
User asks: "Show Q4 tax liability"
    ↓
Orchestrator analyzes query
    ↓
Routes to CTAX MCP
    ↓
CTAX queries lakehouse (semantic search)
    ↓
Retrieves relevant documents
    ↓
Sends to Mixtral with customer LoRA
    ↓
Mixtral generates answer
    ↓
Returns to user with sources
```

### 4. Continuous Learning Loop

```
User interaction logs
    ↓
Query + Answer + Feedback
    ↓
Training dataset accumulation
    ↓
Daily LoRA training
    ↓
New LoRA version deployed
    ↓
Mixtral gets smarter at customer's domain
    ↓
Repeat ∞
```

---

## 🏗️ Component Status

### ✅ Implemented
- [x] Claude Sonnet 4.5 handler generator
- [x] Complete ingestion pipeline
- [x] Delta Lake storage
- [x] Lance vector DB
- [x] MCP SDK & base classes
- [x] LoRA manager (hot-swap code)
- [x] Model manager (LRU eviction)
- [x] Onboarding UI (file upload)
- [x] Console UI
- [x] MinIO storage
- [x] File upload to MinIO

### ⚠️ Partially Implemented
- [~] Per-customer deployment (orchestrator created, not integrated)
- [~] vLLM deployment (docker config ready, not running)
- [~] MCP implementations (CTAX, LAW exist, not deployed per customer)

### ❌ Missing
- [ ] LoRA training pipeline (continuous learning)
- [ ] Ray Serve MCP orchestration
- [ ] Per-customer docker-compose generator (created, needs integration)
- [ ] Ingestion trigger on file upload
- [ ] Self-hosted installer package
- [ ] Deployment mode selection UI

---

## 🎯 Two Deployment Modes

### Mode 1: Managed (SaaS)
**You host everything:**
```
Your Infrastructure:
├── Customer EATON
│   ├── Mixtral instance (your GPU)
│   ├── Lakehouse (your storage)
│   └── Console (your servers)
├── Customer e-ProCat
│   └── (separate stack)
└── ... more customers
```

**Advantages:**
- You manage updates
- Elastic scaling
- Centralized monitoring

**Customer accesses via**: https://eaton.0711.cloud

### Mode 2: Self-Hosted (On-Premise)
**Customer runs everything:**
```
EATON's Infrastructure:
├── Download 0711 installer
├── Run on their servers
├── Air-gapped possible
├── Full data sovereignty
└── License key validation

Access: http://eaton-internal-server
```

**Advantages:**
- Complete data privacy
- Air-gap capable
- Regulatory compliance
- No internet dependency

**Installer**: `install-0711.sh` (to be created)

---

## 💡 Key Innovations

### 1. Adaptive Import (Claude)
Handles **any** file format automatically:
- SAP proprietary exports
- Legacy DATEV formats
- Custom XML schemas
- Weird Excel structures
- **No developer needed!**

### 2. Personalized AI Brain (LoRA)
Each customer's Mixtral learns their:
- Industry terminology
- Business processes
- Data patterns
- Query preferences

After 1 month: EATON's Mixtral knows EATON's business better than any consultant.

### 3. Full RAG Stack
Not just vector search:
- **Structured** (Delta Lake): SQL queries on data
- **Semantic** (Lance): "Find similar contracts"
- **Graph** (Neo4j): "Who knows this client?"
- **Hybrid**: Combine all three

### 4. MCP Orchestration
AI routes queries to right specialist:
- Tax question → CTAX MCP
- Contract question → LAW MCP
- Product question → ETIM MCP
- Complex: Multiple MCPs in sequence

---

## 📊 Resource Requirements

### Per Customer (Managed Mode)
- **GPU**: 30GB (24GB Mixtral + 4GB embeddings + 2GB LoRA)
- **RAM**: 32GB
- **Storage**: 100GB base + customer data
- **Network**: 1 Gbps

### Self-Hosted (Customer's Hardware)
- **Minimum**: 1x A100 40GB or 2x RTX 4090
- **Recommended**: 1x A100 80GB
- **CPU**: 16+ cores
- **RAM**: 64GB+
- **Storage**: 500GB+ SSD

---

## 🚀 Next Steps to Complete

1. **Integrate deployment orchestrator** into onboarding API
2. **Wire file upload** → ingestion trigger
3. **Build LoRA training pipeline** (daily fine-tuning)
4. **Create self-hosted installer** package
5. **Add deployment mode** to onboarding UI
6. **Deploy test customer** (EATON or e-ProCat)
7. **Verify complete flow** end-to-end

---

## 🎓 Customer Experience

### Managed (SaaS):
1. Go to 0711.cloud/onboarding
2. Upload data (files/folders)
3. Select MCPs
4. Wait 10 minutes (deployment + ingestion)
5. Access console at eaton.0711.cloud
6. Start chatting with their AI brain

### Self-Hosted (On-Premise):
1. Download install-0711.sh
2. Run: `sudo ./install-0711.sh --license=ENTERPRISE-EATON-2025`
3. Select data folders
4. Wait 15 minutes (pulls Docker images, processes data)
5. Access at http://localhost:3000
6. Start chatting

---

**Status**: Architecture complete, core built, deployment automation next! 🚀
