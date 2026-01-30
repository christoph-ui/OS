# 🏭 Bosch Complete Integration Plan
## Migration + LoRA Training + Mother of All RAGs

**Status**: 🚀 **IN PROGRESS** - Phase 1 Foundation Complete
**Timeline**: 6 weeks
**Last Updated**: 2025-12-06

---

## 🎯 Executive Summary

Complete integration of Bosch Thermotechnik as 0711-OS's first manufacturing client, including:
1. **Full data migration** (23K products, 17K embeddings, 5K graph edges)
2. **3 specialized LoRA adapters** for HVAC domain expertise
3. **Mother of All Bosch RAGs** - State-of-the-art multi-modal retrieval system

**Expected Outcomes**:
- ✅ Bosch products searchable via console (<2 sec response time)
- ✅ 3 production LoRA adapters (terminology, classification, extraction)
- ✅ Complete RAG with SQL + Vector + Graph + Documents + Images
- ✅ 90%+ accuracy on ECLASS/ETIM classification
- ✅ Foundation for 50+ manufacturing clients

---

## 📋 Project Phases

### ✅ Phase 0: Foundation (COMPLETE - Week 0)
- [x] Client directory structure created
- [x] NLP parser ported (31 regex patterns)
- [x] ECLASS/ETIM shared utilities built
- [x] Configuration system setup
- [x] Documentation framework

**Files Created**: 8 core files, ~1,200 lines of code
**Time**: 2 hours

---

### 🔄 Phase 1: Data Migration (IN PROGRESS - Week 1-2)

#### 1.1 Database Export
**Source**: Bosch PostgreSQL (localhost:5434)
- [ ] Export 23,138 products to Parquet format
- [ ] Export 17,716 embeddings to numpy arrays
- [ ] Export 5,000 graph relationships to JSON
- [ ] Export ECLASS/ETIM classifications
- [ ] Export metadata (quality scores, sources, timestamps)

**Scripts Needed**:
```python
lakehouse/migrations/bosch_export.py
lakehouse/migrations/bosch_import.py
```

#### 1.2 Lakehouse Setup
**Target**: `lakehouse/clients/bosch/`
- [ ] Create Delta Lake tables (products, features, classifications)
- [ ] Setup LanceDB with proper indexing (384D cosine similarity)
- [ ] Create Neo4j database for Bosch graph
- [ ] Build performance indexes

**Storage Estimate**: ~500GB total

#### 1.3 BoschProductMCP Development
**Location**: `mcps/core/bosch_product.py`
- [ ] Port 9 MCP tools:
  - `search_products` (SQL full-text)
  - `search_similar_products` (Vector)
  - `get_product` (By ID)
  - `get_related_products` (Graph)
  - `execute_sql` (Direct SQL)
  - `get_statistics` (Stats)
  - `get_etim_groups` (ETIM classes)
  - `search_by_etim_group` (Filter)
  - `execute_cypher` (Graph queries)
- [ ] Adapt to Delta/Lance/Neo4j backends
- [ ] Register in MCP registry
- [ ] Test via console

**Deliverable**: Bosch data fully queryable via 0711-OS

**Week 1-2 Success Criteria**:
- ✅ All 23,138 products in Delta Lake
- ✅ All embeddings in LanceDB with indexes
- ✅ Graph in Neo4j
- ✅ MCP tools working
- ✅ <100ms query latency

---

### 🧠 Phase 2: LoRA Training (Week 2-3)

#### LoRA #1: Bosch HVAC Terminology Specialist

**Purpose**: German HVAC terminology + Bosch product codes

**Training Data Preparation**:
```python
# Generate 5,000 instruction pairs
{
  "instruction": "Was ist das GC9800iW 30 P 23?",
  "input": "",
  "output": "Das Condens GC9800iW 30 P 23 ist ein Gas-Brennwertgerät..."
}
```

**Sources**:
- 23,138 product descriptions
- Product codes and naming patterns
- German HVAC terminology database
- Feature descriptions

**Training Config**:
```yaml
base_model: mistralai/Mixtral-8x7B-Instruct-v0.1
lora_rank: 64
lora_alpha: 128
learning_rate: 2e-4
batch_size: 4
gradient_accumulation: 4
epochs: 3
dataset_size: 5000
```

**Training**:
- [ ] Generate 5,000 training examples
- [ ] Train on dual H200s (3-4 hours)
- [ ] Evaluate on German HVAC queries
- [ ] Deploy to vLLM

**Deliverable**: `adapters/bosch-terminology-lora-v1` (~200MB)

**Success Metrics**:
- 95%+ accuracy on Bosch product name recognition
- Correctly handles German HVAC terms
- 30%+ improvement in semantic search relevance

---

#### LoRA #2: ECLASS/ETIM Classification Expert

**Purpose**: Automate ECLASS 15.0 / ETIM 10.0 classification

**Training Data Preparation**:
```python
# Expand from 773 to 2,000 examples
{
  "instruction": "Classify with ECLASS 15.0 and ETIM 10.0",
  "input": "Gas-Brennwertgerät Condens GC9800iW, 30 kW...",
  "output": {
    "eclass_id": "AEI482013",
    "eclass_name": "Gas condensing boiler",
    "eclass_irdi": "0173-1#01-AEI482013#015",
    "etim_class": "EC010232",
    "etim_name": "Central heating boiler gas",
    "confidence": 0.95
  }
}
```

**Sources**:
- 773 existing ETIM conversions (from etim-lora-training)
- 6 ECLASS examples → expand to 200+
- ECLASS 15.0 reference (5,640 classes)
- ETIM 10.0 reference (17,377 features)
- Synthetic examples from templates

**Training Config**:
```yaml
base_model: mistralai/Mixtral-8x7B-Instruct-v0.1
lora_rank: 64
lora_alpha: 128
learning_rate: 2e-4
batch_size: 4
epochs: 3
dataset_size: 2000
```

**Training**:
- [ ] Expand dataset to 2,000 examples
- [ ] Build on etim-lora-training work
- [ ] Train on dual H200s (4-5 hours)
- [ ] Validate against expert classifications
- [ ] Deploy to vLLM

**Deliverable**: `adapters/bosch-eclass-etim-lora-v1` (~200MB)

**Success Metrics**:
- 90%+ accuracy on ECLASS/ETIM classification
- Reduces OpenAI API costs by 80%
- Classifications match expert validation

---

#### LoRA #3: Technical Specification Extractor

**Purpose**: Extract structured specs from German technical text

**Training Data Preparation**:
```python
# Generate 10,000 examples from NLP parser
{
  "instruction": "Extract technical specifications",
  "input": "Nennwärmeleistung 50/30: 4,2 - 30,0 kW, Höhe: 850 mm, Breite: 440 mm...",
  "output": {
    "heat_output_50_30_min": {"value": 4.2, "unit": "kW", "confidence": 0.95},
    "heat_output_50_30_max": {"value": 30.0, "unit": "kW", "confidence": 0.95},
    "height": {"value": 850, "unit": "mm", "confidence": 0.95},
    "width": {"value": 440, "unit": "mm", "confidence": 0.95}
  }
}
```

**Sources**:
- 23,138 product descriptions
- NLP parser outputs (31 patterns)
- Unit conversions and normalizations
- Derived value calculations

**Training Config**:
```yaml
base_model: mistralai/Mixtral-8x7B-Instruct-v0.1
lora_rank: 64
lora_alpha: 128
learning_rate: 2e-4
batch_size: 4
epochs: 3
dataset_size: 10000
```

**Training**:
- [ ] Generate 10,000 training examples
- [ ] Include derived values (modulation ratio, CO2)
- [ ] Train on dual H200s (3-4 hours)
- [ ] Compare against NLP parser baseline
- [ ] Deploy to vLLM

**Deliverable**: `adapters/bosch-spec-extractor-lora-v1` (~150MB)

**Success Metrics**:
- 90%+ spec extraction accuracy vs. NLP parser
- Handles variations in German technical writing
- Correctly calculates derived values

---

### 🏆 Phase 3: Mother of All Bosch RAGs (Week 3-4)

#### 3.1 Multi-Modal Retrieval Architecture

```
USER QUERY: "Finde Gas-Brennwertgeräte mit 30kW für Gewerbebau"
    ↓
┌─────────────────────────────────────────────────────────┐
│ QUERY UNDERSTANDING (Terminology LoRA)                  │
│  - "Gas-Brennwertgeräte" = gas condensing boilers      │
│  - "30kW" = nominal heat output                         │
│  - "Gewerbebau" = commercial building                   │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ PARALLEL RETRIEVAL (3 sources)                         │
│                                                         │
│  SQL (Delta)     Vector (Lance)    Graph (Neo4j)      │
│  Filter by       Semantic          Related products    │
│  power, type     similarity        accessories        │
│  ↓               ↓                  ↓                  │
│  50 results      30 results        20 results         │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ ENRICHMENT (Classification LoRA)                       │
│  - Verify ECLASS/ETIM                                  │
│  - Extract missing specs (Spec Extractor LoRA)        │
│  - Quality scoring                                     │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ DOCUMENT RETRIEVAL                                      │
│  - Datasheets (PDF chunks)                             │
│  - Manuals (page-level)                                │
│  - Images (CLIP embeddings)                            │
│  - CAD drawings (Qwen2-VL analysis)                    │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ FUSION & RANKING                                        │
│  - Hybrid score (RRF algorithm)                        │
│  - Deduplication                                       │
│  - Top 10 results                                      │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ GENERATION (Mixtral + LoRA)                            │
│  - Load appropriate LoRA                               │
│  - Generate comprehensive answer                       │
│  - Include citations                                   │
└─────────────────────────────────────────────────────────┘
```

#### 3.2 Data Storage Structure

```
lakehouse/clients/bosch/
├── delta/
│   ├── products/                   # 23,138 products
│   ├── documents/                  # Document metadata
│   └── relationships/              # Graph edges as table
│
├── vector/                         # LanceDB
│   ├── product_embeddings/         # 23,138 x 384D
│   ├── document_chunks/            # 15,000+ chunks
│   └── image_embeddings/           # CLIP 512D
│
└── graph/                          # Neo4j
    ├── products/                   # 23,138 nodes
    ├── categories/                 # Category hierarchy
    └── relationships/              # 5,000+ edges
```

#### 3.3 Implementation Tasks

**Multi-Modal Retrieval**:
- [ ] Build SQL search (Delta Lake)
- [ ] Build vector search (LanceDB with cosine similarity)
- [ ] Build graph search (Neo4j Cypher)
- [ ] Implement RRF fusion algorithm
- [ ] Add result deduplication

**Document Processing**:
- [ ] PDF datasheet ingestion pipeline
- [ ] Installation manual chunking
- [ ] Image processing with CLIP
- [ ] CAD drawing analysis with Qwen2-VL
- [ ] Technical table extraction

**LoRA Orchestration**:
- [ ] Implement hot-swapping logic
- [ ] Create routing based on task type
- [ ] Add performance monitoring
- [ ] Cache frequently-used LoRAs

**API Layer**:
- [ ] `/api/bosch/search` - Multi-modal search
- [ ] `/api/bosch/classify` - Classification with LoRA
- [ ] `/api/bosch/extract-specs` - Spec extraction with LoRA
- [ ] `/api/bosch/related` - Graph traversal

**Deliverable**: Complete Mother of All Bosch RAGs

**Success Metrics**:
- Retrieval recall@10: >85%
- Answer relevance: >90% (human eval)
- Response time: <2 seconds
- Source citation accuracy: 100%

---

### ✅ Phase 4: Integration & Testing (Week 4-5)

#### 4.1 Console Integration
- [ ] Add Bosch to client selector
- [ ] Build product search interface
- [ ] Display product cards (images, specs, docs)
- [ ] Show graph relationships visually
- [ ] Enable LoRA model selection dropdown

#### 4.2 End-to-End Testing
- [ ] Test complete RAG pipeline with 50 real queries
- [ ] Validate retrieval accuracy (precision/recall)
- [ ] Test LoRA hot-swapping (<1 sec)
- [ ] Benchmark response times
- [ ] Verify NO mock data (quality check)

#### 4.3 Performance Optimization
- [ ] Index tuning (Delta, Lance, Neo4j)
- [ ] Caching strategy (frequently accessed products)
- [ ] LoRA pre-loading (terminology always loaded)
- [ ] Query optimization

#### 4.4 Documentation
- [ ] API documentation (Swagger/OpenAPI)
- [ ] User guide for Bosch console
- [ ] LoRA training playbooks
- [ ] RAG architecture diagrams

**Success Criteria**:
- All tests passing
- <2 second end-to-end response time
- 90%+ user satisfaction (sample testing)
- Complete documentation

---

### 🚀 Phase 5: Production Launch (Week 5-6)

#### 5.1 Deployment
- [ ] Deploy to production environment
- [ ] Setup monitoring (Prometheus/Grafana)
- [ ] Configure alerts (latency, errors)
- [ ] Enable logging (requests, responses, LoRA swaps)

#### 5.2 User Training
- [ ] Train Bosch users on console
- [ ] Provide query examples
- [ ] Share best practices
- [ ] Collect feedback

#### 5.3 Continuous Learning Setup
- [ ] Log all queries and responses
- [ ] Track user feedback (thumbs up/down)
- [ ] Setup daily LoRA retraining pipeline
- [ ] Enable A/B testing (with/without LoRAs)

**Deliverable**: Production-ready Bosch client

---

## 📊 Progress Tracking

### Overall Progress: 15% Complete

| Phase | Status | Progress | ETA |
|-------|--------|----------|-----|
| 0. Foundation | ✅ Complete | 100% | Done |
| 1. Migration | 🔄 In Progress | 10% | Week 2 |
| 2. LoRA Training | ⏳ Pending | 0% | Week 3 |
| 3. Mother RAG | ⏳ Pending | 0% | Week 4 |
| 4. Testing | ⏳ Pending | 0% | Week 5 |
| 5. Launch | ⏳ Pending | 0% | Week 6 |

### Current Sprint (Week 1): Data Migration
- [x] Foundation complete
- [ ] PostgreSQL export
- [ ] Lakehouse setup
- [ ] Data import
- [ ] BoschProductMCP

---

## 🎯 Key Deliverables

### Code Artifacts
1. ✅ `clients/bosch/` - Client namespace
2. ✅ `mcps/shared/eclass_etim.py` - ECLASS/ETIM utilities
3. ✅ `clients/bosch/nlp/parser.py` - NLP parser
4. 🔄 `mcps/core/bosch_product.py` - BoschProductMCP
5. 🔄 `lakehouse/migrations/bosch_*.py` - Migration scripts
6. 🔄 `adapters/bosch-*-lora-v1/` - 3 LoRA adapters
7. 🔄 RAG pipeline implementation
8. 🔄 API endpoints

### Data Assets
- 23,138 products in Delta Lake
- 23,138 embeddings in LanceDB
- 5,000+ graph edges in Neo4j
- 15,000+ document chunks
- Image/CAD embeddings

### AI Models
- `bosch-terminology-lora-v1` (200MB)
- `bosch-eclass-etim-lora-v1` (200MB)
- `bosch-spec-extractor-lora-v1` (150MB)

### Documentation
- ✅ Bosch client README (400+ lines)
- ✅ Migration summary
- 🔄 LoRA training guides
- 🔄 RAG architecture docs
- 🔄 API documentation

---

## 💰 Cost-Benefit Analysis

### Investment
| Item | Cost |
|------|------|
| Engineering time | 6 weeks |
| GPU training (15 hours) | ~$50 (local H200s) |
| Storage (500GB) | ~$10/month |
| **Total** | **~6 weeks + $60** |

### Returns
| Benefit | Value |
|---------|-------|
| Faster search | <2 sec vs 5-10 sec |
| Cost savings | $200/month (OpenAI) |
| Better accuracy | 90% vs 75% |
| Reusable assets | ECLASS/ETIM for 50+ clients |
| Foundation | Manufacturing vertical |

**ROI**: Break-even in 1 month, massive long-term value

---

## 🎓 Learnings & Reusability

### Patterns Created
1. **Client isolation architecture** - Template for all clients
2. **Multi-modal RAG** - SQL + Vector + Graph + Documents
3. **LoRA orchestration** - Hot-swapping, task routing
4. **ECLASS/ETIM support** - Reusable for all manufacturing

### Reusable for Other Clients
- **Manufacturing**: ECLASS/ETIM LoRA, NLP patterns
- **Any Client**: Multi-modal RAG architecture
- **Platform**: LoRA training pipeline, hot-swapping

---

## 📞 Team & Communication

**Project Lead**: Claude Code + Christoph
**Timeline**: 6 weeks (2025-12-06 to 2026-01-17)
**Status Updates**: Weekly
**Documentation**: Real-time (this file)

**Communication Channels**:
- Planning: This document
- Progress: Todo list
- Technical: Code comments
- Decisions: Git commits

---

## 🏆 Success Criteria (Final)

### Technical
- [ ] 100% data migrated (23,138 products)
- [ ] 3 LoRA adapters trained and deployed
- [ ] Complete RAG pipeline operational
- [ ] <2 second response time
- [ ] 90%+ retrieval accuracy
- [ ] All tests passing

### Business
- [ ] Bosch accessible via console
- [ ] Users trained and satisfied
- [ ] Cost savings realized ($200/month)
- [ ] Foundation for manufacturing vertical
- [ ] Documentation complete

### Quality
- [ ] NO mock data (enforced)
- [ ] 90%+ data completeness
- [ ] Source citations 100% accurate
- [ ] Performance monitoring active

---

**Last Updated**: 2025-12-06
**Next Review**: 2025-12-13 (Weekly)
**Status**: 🚀 IN PROGRESS - Foundation Complete, Starting Migration

---

*This is the master plan. All work references back to this document.*