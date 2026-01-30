# 0711 Intelligence Platform - Claude Code Context

**Version**: 1.0.0
**Last Updated**: 2025-11-28
**Project Type**: Enterprise AI Platform (RAG + Fine-tuning SaaS)

---

## 🎯 Project Overview

The **0711 Intelligence Platform** is an AI-first enterprise operating system that provides **personalized AI brains** for customers through:

1. **Per-customer isolated AI instances** (Mixtral 8x7B + LoRA fine-tuning)
2. **Adaptive data ingestion** (Claude Sonnet 4.5 generates import handlers for ANY file format)
3. **Full RAG stack** (Delta Lake + LanceDB + Neo4j Graph)
4. **MCP (Model Context Protocol) orchestration** for domain-specific AI experts
5. **Two deployment modes**: Managed SaaS + Self-hosted on-premise

### Business Model
- **German market focus** (B2B, DSGVO compliant)
- **Usage-based SaaS** (Databricks-style land and expand)
- **Continuous learning**: Each customer's AI improves from their specific data

---

## 📁 Project Structure

```
0711-OS/
├── api/                          # Control Plane API (Customer mgmt & billing)
│   ├── models/                   # SQLAlchemy models (customers, subscriptions, experts)
│   ├── routes/                   # FastAPI endpoints (auth, billing, onboarding)
│   ├── services/                 # Business logic (Stripe, email, licensing)
│   └── main.py                   # Control Plane FastAPI app (Port 4080)
│
├── console/                      # Customer-facing console
│   ├── frontend/                 # Next.js 14 + React + TypeScript (Port 4020)
│   │   ├── src/app/             # App router (chat, data, settings)
│   │   └── src/components/      # UI components (shadcn/ui style)
│   └── backend/                  # Console Backend API (Port 4010)
│       ├── routes/              # chat.py, ingest.py, data.py, mcps.py
│       ├── websocket/           # WebSocket for real-time chat
│       └── main.py              # Console FastAPI app
│
├── ingestion/                    # Data ingestion pipeline
│   ├── crawler/                 # File crawlers + handlers (PDF, DOCX, CSV, etc.)
│   │   ├── file_crawler.py     # Main crawler orchestrator
│   │   └── file_handlers/      # 10+ built-in + Claude-generated handlers
│   ├── classifier/              # Classify docs to MCPs (CTAX, LAW, ETIM)
│   ├── processor/               # Chunking + embedding
│   │   ├── chunker.py          # Structure-aware chunking
│   │   └── embedder.py         # multilingual-e5-large embeddings
│   └── loader/                  # Load to lakehouse (Delta + Lance + Graph)
│
├── lakehouse/                    # Multi-modal data storage
│   ├── delta/                   # Delta Lake (structured tables)
│   ├── vector/                  # LanceDB (vector embeddings)
│   │   └── lance_store.py      # Vector search implementation
│   ├── graph/                   # Neo4j integration (entity relationships)
│   └── storage/                 # MinIO/S3 interface
│
├── inference/                    # Model serving
│   ├── server.py                # vLLM server (Mixtral 8x7B)
│   ├── lora_manager.py          # Hot-swappable LoRA adapters (<1s)
│   ├── embedding_server.py      # Embedding service
│   └── Dockerfile               # GPU-enabled container
│
├── mcps/                         # Model Context Protocol system
│   ├── sdk/                     # MCP SDK (base classes, decorators)
│   │   ├── base_mcp.py         # BaseMCP class
│   │   └── decorators.py       # @tool, @resource decorators
│   ├── core/                    # Core MCPs
│   │   ├── ctax.py             # Corporate tax specialist
│   │   ├── law.py              # Legal contracts specialist
│   │   └── tender.py           # Public tender specialist
│   └── registry.py              # MCP discovery & routing
│
├── orchestrator/                 # AI orchestration
│   ├── mcp/                     # MCP routing & model management
│   │   └── model_manager.py    # LRU eviction, GPU memory management
│   ├── langgraph/               # LangGraph workflow orchestration
│   └── pipelines/               # Pre-built orchestration pipelines
│
├── provisioning/                 # Deployment automation
│   ├── api/                     # Provisioning API
│   ├── installer/               # Self-hosted installer
│   └── wizard/                  # Onboarding wizard
│
├── tests/                        # Test suite
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   └── e2e/                     # End-to-end tests
│
├── core/                         # Shared core utilities
│   ├── config.py                # Configuration management
│   └── __init__.py              # Platform class
│
├── apps/                         # Public websites
│   ├── website/                 # Marketing + onboarding (Next.js, Port 4000)
│   │   ├── app/page.tsx        # Homepage (manifesto, vision, features)
│   │   ├── app/builders/       # "Built for Builders" page (personas + satire)
│   │   ├── app/pricing/        # Transparent pricing
│   │   └── app/experts/        # Expert network marketplace
│   └── admin/                   # Admin dashboard mockup
│
├── migrations/                   # Alembic database migrations
├── deployment/                   # Kubernetes/Docker configs
├── scripts/                      # Utility scripts
│
├── docker-compose.yml           # Full stack orchestration
├── requirements.txt             # Python dependencies
├── pyproject.toml              # Project metadata + dev tools
├── .env.example                # Environment template
├── START_ALL.sh                # Start entire platform (dev)
└── STOP_ALL.sh                 # Stop all services
```

---

## 🏗️ Architecture

### Complete Data Flow

```
1. FILE UPLOAD → ADAPTIVE INGESTION
   User uploads proprietary .DAT file
   ↓
   MinIO: customer-eaton/raw/
   ↓
   Claude Sonnet 4.5 analyzes file structure
   ↓
   Generates Python import handler (on-the-fly)
   ↓
   Validates & registers handler
   ↓
   Extracts data → Lakehouse

2. DATA PROCESSING → RAG PIPELINE
   Files in MinIO
   ↓
   Crawl & Extract (crawler + handlers)
   ↓
   Classify to MCPs (CTAX, LAW, ETIM)
   ↓
   Chunk intelligently (structure-aware)
   ↓
   Embed (multilingual-e5-large)
   ↓
   Load to Lakehouse:
      ├── Delta Lake: Structured tables
      ├── LanceDB: Vector search
      └── Neo4j: Entity graph

3. QUERY → MCP ORCHESTRATION
   User: "Show Q4 tax liability"
   ↓
   Orchestrator analyzes query
   ↓
   Routes to CTAX MCP
   ↓
   CTAX queries lakehouse (hybrid search)
   ↓
   Retrieves relevant docs
   ↓
   Sends to Mixtral + customer LoRA
   ↓
   Returns answer with sources

4. CONTINUOUS LEARNING
   User interactions logged
   ↓
   Query + Answer + Feedback
   ↓
   Training dataset accumulation
   ↓
   Daily LoRA training
   ↓
   New LoRA version deployed
   ↓
   Customer's AI gets smarter ∞
```

### Per-Customer Isolation

**Deployment Model**: **Hybrid Isolation**
- **Per-customer containers**: vLLM (with customer LoRA), embeddings, lakehouse
- **Shared services**: MCPs (ETIM, CTAX, LAW) accessed via MCP Router
- **Result**: 3 containers per customer instead of 7+ (60% reduction)

**Port Allocation Strategy**
Each customer gets a 100-port block calculated by:
```python
base_port = 5000 + (hash(customer_id) % 50) * 100
```

**Example: EATON Deployment (Actual Production)**
```
Per-Customer Stack (3 containers):
├── eaton-vllm (port 9300)
│   ├── Mixtral 8x7B-Instruct with EATON LoRA
│   ├── GPU: H200 NVL GPU 1 (40% memory utilization)
│   └── LoRA enabled (rank 64, hot-swappable)
├── eaton-embeddings (port 9301)
│   ├── multilingual-e5-large (CPU-based)
│   └── Model pre-downloaded (instant startup)
└── eaton-lakehouse (port 9302)
    ├── HTTP API for Delta Lake + LanceDB
    ├── Mounts: /tmp/lakehouse/eaton/
    ├── Data: 21 documents, 31,807 chunks, 170MB
    └── Status: ✅ Healthy and serving data

Shared Services (accessed via MCP Router):
├── ETIM MCP (port 7779) - Product classification
│   ├── Type: Shared (one instance for all customers)
│   ├── Location: /home/christoph.bertsch/0711/0711-etim-mcp/
│   ├── Status: Up 2 weeks (healthy)
│   └── Enabled for EATON via database flag
└── Customer accesses via: GET /api/mcp-services/query

Data Isolation:
├── MinIO Bucket: customer-eaton (completely isolated)
├── Lakehouse: /tmp/lakehouse/eaton/ (customer-specific)
└── MCP queries include customer context (query-level isolation)
```

**Benefits of Shared MCP Architecture**:
- ✅ **60% fewer containers** per customer (3 vs 7+)
- ✅ **Faster deployments** (<2 min vs 15 min)
- ✅ **Easy MCP updates** (update once, all customers benefit)
- ✅ **Lower costs** (shared infrastructure)
- ✅ **Independent roadmaps** (MCPs evolve separately)

**Complete Isolation**: Customer data never mixes (enforced at lakehouse level + query context)

See implementation:
- `provisioning/api/services/deployment_orchestrator.py:39` (deployment)
- `orchestrator/mcp/mcp_router.py` (shared MCP routing)
- `api/routes/mcp_services.py` (MCP marketplace API)

---

## 🔧 Technology Stack

### Backend (Python 3.11+)
- **FastAPI**: Web framework (2 separate apps: Control Plane + Console)
- **SQLAlchemy**: ORM + PostgreSQL
- **Alembic**: Database migrations
- **Pydantic**: Data validation
- **Redis**: Caching + pub/sub

### Frontend (TypeScript)
- **Next.js 14**: React framework (App Router)
- **React 18**: UI library
- **Tailwind CSS**: Styling
- **Lucide React**: Icons
- **WebSocket**: Real-time chat

### AI/ML Stack
- **vLLM**: Model serving (Mixtral 8x7B-Instruct)
- **LoRA**: Fine-tuning (hot-swappable adapters)
- **sentence-transformers**: Embeddings (multilingual-e5-large)
- **Claude Sonnet 4.5**: Adaptive handler generation
- **Ray Serve**: Distributed MCP orchestration (planned)

### Lakehouse
- **Delta Lake**: ACID transactions on data lake
- **LanceDB**: Columnar vector database
- **Neo4j**: Graph database (planned)
- **MinIO**: S3-compatible object storage
- **PyArrow**: Columnar data processing

### Infrastructure
- **Docker**: Containerization
- **PostgreSQL 16**: Relational database
- **Redis 7**: Caching
- **MinIO**: Object storage
- **NVIDIA GPU**: Model inference (A100 recommended)

### Payments & Compliance
- **Stripe**: Payment processing
- **WeasyPrint**: German invoice PDF generation
- **DSGVO/GDPR**: Compliance built-in

---

## ⚠️ CRITICAL: Persistent Data Storage Rules

**Created**: 2026-01-11 after /tmp disaster (Eaton data lost on reboot)

### THE COMMANDMENTS

#### ❌ THOU SHALT NOT:

1. **NEVER use `/tmp` for persistent data**
   ```python
   # ❌ WRONG - Data lost on reboot
   lakehouse_path = Path(f"/tmp/lakehouse/{customer_id}")
   lora_path = Path(f"/tmp/loras/{customer_id}")
   ```

   **Why**: `/tmp` is ephemeral and gets wiped on:
   - Server reboots
   - System updates
   - Cleanup scripts
   - Container restarts

2. **NEVER hardcode paths in business logic**
   ```python
   # ❌ WRONG - Violates separation of concerns
   def ingest_data(customer_id):
       path = f"/data/lakehouse/{customer_id}"  # Hardcoded!
   ```

3. **NEVER skip Docker volumes for containers**
   ```yaml
   # ❌ WRONG - Bind mount to /tmp
   volumes:
     - /tmp/lakehouse/eaton:/data/lakehouse
   ```

#### ✅ THOU SHALL:

1. **ALWAYS use `CustomerPaths` for all customer data**
   ```python
   # ✅ CORRECT - Centralized, deployment-aware
   from core.paths import CustomerPaths

   lakehouse_path = CustomerPaths.get_lakehouse_path(customer_id)
   lora_path = CustomerPaths.get_lora_path(customer_id)
   ```

2. **ALWAYS use Docker volumes for managed deployments**
   ```yaml
   # ✅ CORRECT - Persistent Docker volumes
   volumes:
     customer-lakehouse-data: {}
     customer-lora-adapters: {}

   services:
     lakehouse:
       volumes:
         - customer-lakehouse-data:/data/lakehouse  # Survives reboots!
         - customer-lora-adapters:/data/loras
   ```

3. **ALWAYS verify persistence after deployment**
   ```bash
   # Test: Reboot server, data should still exist
   docker volume ls | grep customer
   docker exec customer-lakehouse ls /data/lakehouse
   ```

### Storage Hierarchy

| Data Type | Managed (Docker) | Self-Hosted | Ephemeral? |
|-----------|------------------|-------------|------------|
| **PostgreSQL** (metadata, categories) | `postgres_data` volume | `/var/lib/postgresql/data` | ❌ Persistent |
| **MinIO** (uploaded files) | `minio_data` volume | `/var/lib/0711/minio` | ❌ Persistent |
| **Lakehouse** (embeddings, Delta) | `{customer}-lakehouse-data` volume | `/var/lib/0711/lakehouse/{customer}` | ❌ Persistent |
| **LoRA adapters** (fine-tuned models) | `{customer}-loras` volume | `/var/lib/0711/loras/{customer}` | ❌ Persistent |
| **Temp downloads** (ingestion staging) | `/tmp/ingestion_{customer}_*` | `/tmp/ingestion_{customer}_*` | ✅ OK to lose |

### CustomerPaths API

**File**: `core/paths.py`

```python
from core.paths import CustomerPaths

# Get persistent lakehouse path
lakehouse = CustomerPaths.get_lakehouse_path("eaton")
# Managed: /data/lakehouse (Docker volume)
# Self-hosted: /var/lib/0711/lakehouse/eaton

# Get LoRA path
loras = CustomerPaths.get_lora_path("eaton")
# Managed: /data/loras (Docker volume)
# Self-hosted: /var/lib/0711/loras/eaton

# Get TEMPORARY path (OK to use /tmp)
temp = CustomerPaths.get_temp_path("eaton", prefix="ingestion")
# /tmp/ingestion_eaton_abc123 (will be deleted)

# Validate path is safe
is_safe = CustomerPaths.validate_path_safety(my_path)
# Returns False if path starts with /tmp/
```

### Deployment Type Detection

Set via environment variable:
```bash
# In .env or docker-compose
DEPLOYMENT_TYPE=managed  # Options: managed, self_hosted, development
```

Auto-detection logic:
1. If `DEPLOYMENT_TYPE` set → use it
2. If `/.dockerenv` exists → managed
3. If `/var/lib/0711` exists → self_hosted
4. Else → development

### What Went Wrong (Eaton Case Study)

**The Crime**:
```yaml
# deployments/eaton/docker-compose.yml (BEFORE FIX)
volumes:
  - /tmp/lakehouse/eaton:/data/lakehouse  # ❌ DISASTER
```

**The Consequences**:
- 617 files uploaded to MinIO ✅ (safe, persisted)
- 31,807 embeddings generated ✅ (but stored in /tmp ❌)
- 170MB of Delta Lake tables created ✅ (but in /tmp ❌)
- **Server rebooted → ALL DATA LOST** 💥

**The Fix**:
```yaml
# deployments/eaton/docker-compose.yml (AFTER FIX)
volumes:
  eaton-lakehouse-data: {}  # ✅ Docker volume (persistent)

services:
  lakehouse:
    volumes:
      - eaton-lakehouse-data:/data/lakehouse  # ✅ Survives reboots
```

### Prevention Checklist

Before deploying ANY customer:

- [ ] No `/tmp` references in docker-compose volumes
- [ ] All customer data uses `CustomerPaths`
- [ ] Docker volumes defined for: lakehouse, loras, models
- [ ] `DEPLOYMENT_TYPE` set in environment
- [ ] Health check: `docker volume ls` shows customer volumes
- [ ] Persistence test: Reboot → data survives

### Emergency Recovery

If data lost to /tmp disaster:

1. **Check MinIO** - Raw files should still exist
   ```bash
   docker exec 0711-minio mc ls /data/customer-{customer_id}/
   ```

2. **Re-run ingestion** - Reprocess from MinIO
   ```bash
   python scripts/reimport_{customer}.py
   ```

3. **Verify restoration**
   ```bash
   curl http://localhost:{port}/stats
   # Should show embeddings + tables
   ```

### Files Modified (2026-01-11 Fix)

1. ✅ `core/paths.py` - Created centralized path resolver
2. ✅ `api/routes/upload.py:94` - Use CustomerPaths
3. ✅ `core/customer_registry.py:124,125,180` - Use CustomerPaths
4. ✅ `orchestrator/mcp/mcp_router.py:136` - Use CustomerPaths
5. ✅ `deployments/eaton/docker-compose.yml:83` - Docker volume
6. ✅ `core/config.py:20` - Added deployment_type
7. ✅ `.env.example:47-53` - Added LAKEHOUSE_BASE, LORA_BASE

---

## 🚀 Quick Start

### Development Mode (All Services)

```bash
# 1. Set up environment
cp .env.example .env
# Edit .env with your credentials (HF_TOKEN, DB passwords, etc.)

# 2. Start infrastructure
docker compose up -d postgres redis minio embeddings

# 3. Start all services (Ports 40XX)
./START_ALL.sh

# Services will be available at:
# - Marketing/Onboarding:  http://localhost:4000
# - Console Frontend:      http://localhost:4020
# - Console Backend:       http://localhost:4010
# - Control Plane API:     http://localhost:4080
# - PostgreSQL:            localhost:4005
# - MinIO Console:         http://localhost:4051
```

### Production Mode (Docker Compose)

```bash
# With GPU support (for vLLM)
docker compose --profile gpu up -d

# Without GPU (embeddings only)
docker compose up -d
```

---

## 🔑 Key Components

### 1. Control Plane API (`api/`)
**Port**: 4080
**Purpose**: Customer management, billing, licensing
**Key Files**:
- `api/main.py` - Main FastAPI app
- `api/routes/auth.py` - Authentication (JWT)
- `api/routes/subscriptions.py` - Stripe integration
- `api/routes/onboarding.py` - Customer onboarding wizard
- `api/services/stripe_service.py` - Payment processing

### 2. Console Backend (`console/backend/`)
**Port**: 4010
**Purpose**: Real-time chat, data browsing, ingestion
**Key Files**:
- `console/backend/main.py` - Main FastAPI app
- `console/backend/routes/chat.py` - Chat endpoints + WebSocket
- `console/backend/routes/ingest.py` - Trigger data ingestion
- `console/backend/routes/data.py` - Browse lakehouse data
- `console/backend/websocket/manager.py` - WebSocket connection manager

### 3. Console Frontend (`console/frontend/`)
**Port**: 4020
**Purpose**: Customer-facing UI
**Key Files**:
- `src/app/page.tsx` - Chat interface
- `src/app/data/page.tsx` - Data explorer
- `src/components/Chat.tsx` - Chat component (WebSocket)

### 4. Ingestion Pipeline (`ingestion/`)
**Purpose**: Convert any file format → RAG-ready data
**Key Innovation**: Claude Sonnet 4.5 generates import handlers on-the-fly!

**Key Files**:
- `ingestion/crawler/file_crawler.py` - Main orchestrator
- `ingestion/claude_handler_generator.py` - Claude-powered adapter generation
- `ingestion/crawler/file_handlers/` - Built-in handlers (PDF, DOCX, CSV, XML, etc.)
- `ingestion/processor/chunker.py` - Smart chunking (structure-aware)
- `ingestion/processor/embedder.py` - Generate embeddings

**Flow**:
```python
# Example: EATON uploads proprietary .DAT file
file = "eaton_products.dat"
↓
# Claude analyzes structure
handler = generate_handler(file, claude_sonnet_4_5)
↓
# Registers handler for future use
register_handler(".dat", handler)
↓
# Extract, chunk, embed, load
data = handler.extract(file)
chunks = chunker.chunk(data)
embeddings = embedder.embed(chunks)
lance_store.add(embeddings)
```

### 5. Lakehouse (`lakehouse/`)
**Purpose**: Multi-modal data storage (structured + semantic + graph)

**Key Files**:
- `lakehouse/vector/lance_store.py` - Vector search (LanceDB)
- `lakehouse/delta/tables/` - Delta Lake tables
- `lakehouse/storage/` - MinIO integration

**Storage Modes**:
- **Structured**: Delta Lake (SQL queries, ACID transactions)
- **Semantic**: LanceDB (vector similarity search)
- **Graph**: Neo4j (entity relationships) [Planned]

### 6. Inference (`inference/`)
**Purpose**: Serve Mixtral 8x7B with LoRA hot-swapping

**Key Files**:
- `inference/server.py` - vLLM server wrapper
- `inference/lora_manager.py` - Dynamic LoRA loading (<1s swap time)
- `inference/embedding_server.py` - Embedding service

**GPU Requirements**:
- **Minimum**: 30GB (24GB base + 4GB embeddings + 2GB LoRA)
- **Recommended**: A100 80GB or H100

### 7. MCP System (`mcps/`)
**Purpose**: Domain-specific AI experts (Model Context Protocol)

**Key Files**:
- `mcps/sdk/base_mcp.py` - Base MCP class
- `mcps/sdk/decorators.py` - @tool, @resource decorators
- `mcps/core/ctax.py` - Corporate tax specialist
- `mcps/core/law.py` - Legal contracts specialist
- `mcps/core/tender.py` - Public tender specialist
- `mcps/registry.py` - MCP discovery & routing

**How MCPs Work**:
```python
from mcps.sdk import BaseMCP, tool, resource

class CTaxMCP(BaseMCP):
    name = "ctax"
    description = "Corporate tax specialist"

    @tool
    async def calculate_tax_liability(self, year: int, revenue: float):
        # Query lakehouse for tax-relevant docs
        docs = await self.lakehouse.search(f"tax documents {year}")
        # Send to LLM with context
        return await self.llm.query(docs, "Calculate tax liability")

    @resource
    async def get_tax_laws(self, year: int):
        return await self.lakehouse.get_table(f"tax_laws_{year}")
```

### 8. Orchestrator (`orchestrator/`)
**Purpose**: Route queries to correct MCPs + manage GPU resources

**Key Files**:
- `orchestrator/mcp/model_manager.py` - LRU eviction, memory management
- `orchestrator/langgraph/` - LangGraph workflows [Planned]

---

## 📊 Database Schema (PostgreSQL)

### Control Plane Tables

**User Management** (Multi-tenant RBAC):
- `users` - **Individual users** with role-based access control
  - Roles: `platform_admin`, `customer_admin`, `customer_user`
  - Granular permissions (JSONB): `billing.view`, `users.invite`, `mcps.install`, etc.
  - Invitation workflow support
  - Login tracking & security (failed attempts, lockout)
- `customers` - **Company/organization** accounts
  - One-to-many relationship with users
  - `primary_admin_id` → links to primary User
  - `password_hash` DEPRECATED (now in User model)

**Billing & Operations**:
- `subscriptions` - Plans & billing (Stripe integration)
- `deployments` - Customer instances + license keys
- `invoices` - German-compliant invoices
- `usage_metrics` - Usage tracking for billing
- `audit_log` - Audit trail (DSGVO compliance)

**Marketplace**:
- `mcp_developers` - **Third-party MCP developers** (self-service registration)
  - Verification workflow (pending → verified by admin)
  - Stripe Connect integration (70/30 revenue share)
  - Developer stats (total MCPs, installations, ratings)
- `mcps` - MCP marketplace (installable AI tools)
  - `developer_id` → links to third-party developer (null = first-party/0711)
  - Approval workflow: `pending` → `approved`/`rejected` by platform admin
  - `approved_by_id` → tracks which admin approved
- `experts` - Marketplace experts (consultants/specialists)
- `engagements` - Expert-customer engagements
- `tasks` - Task tracking for engagements
- `mcp_installations` - Track which customers installed which MCPs

### Lakehouse Tables (Delta Lake)
- `documents` - Ingested documents metadata
- `chunks` - Text chunks from documents
- `entities` - Extracted entities (companies, people, dates)
- `relationships` - Entity relationships

---

## 🌐 API Endpoints

### Control Plane API (Port 4080)

**Authentication**
- `POST /api/auth/signup` - Register customer (creates Customer + primary admin User)
- `POST /api/auth/login` - JWT login (queries User table, returns user + customer info)
- `POST /api/auth/verify-email` - Email verification

**User Management** (Team Members)
- `GET /api/users/` - List team members (customer_admin only)
- `POST /api/users/invite` - Invite team member (sends invitation email)
- `POST /api/users/accept-invitation` - Accept invitation & set password
- `GET /api/users/{user_id}` - Get user details
- `PATCH /api/users/{user_id}` - Update user (role, permissions, status)
- `DELETE /api/users/{user_id}` - Remove user (soft delete)
- `POST /api/users/change-password` - Change own password
- `PATCH /api/users/{user_id}/permissions` - Update permissions

**MCP Developer Portal** (Third-party developers)
- `POST /api/mcp-developers/register` - Self-service developer registration
- `GET /api/mcp-developers/me` - Get developer profile
- `GET /api/mcp-developers/{id}` - Get developer by ID
- `POST /api/mcp-developers/mcps` - Submit MCP for approval
- `GET /api/mcp-developers/mcps/my` - List my MCPs

**Platform Admin** (MCP Marketplace Moderation)
- `GET /api/admin/mcp-developers/pending` - List pending developer applications
- `POST /api/admin/mcp-developers/{id}/verify` - Verify (approve) developer
- `POST /api/admin/mcp-developers/{id}/reject` - Reject developer application
- `GET /api/admin/mcps/pending` - List pending MCP submissions
- `POST /api/admin/mcps/{id}/approve` - Approve MCP for marketplace
- `POST /api/admin/mcps/{id}/reject` - Reject MCP (with reason)
- `GET /api/admin/mcps/stats` - Marketplace statistics

**Onboarding**
- `POST /api/onboarding/start` - Start wizard
- `POST /api/onboarding/deploy` - Complete onboarding & deploy
- `GET /api/onboarding/status/{deployment_id}` - Check deployment status
- `GET /api/onboarding/verify/{customer_id}` - Verify deployment and get service URLs

**File Upload** (3 endpoints available)
- `POST /api/upload/files` - Synchronous upload (returns after MinIO upload, ingestion runs in background)
- `POST /api/upload-async/start` - Async upload (returns job_id immediately, poll for status)
- `GET /api/upload-async/status/{job_id}` - Poll async upload status
- `GET /api/upload/list` - List uploaded files
- `DELETE /api/upload/clear` - Clear all uploads (dev only)

**Subscriptions**
- `POST /api/subscriptions/create` - Create (Stripe)
- `GET /api/subscriptions/current` - Get current plan
- `POST /api/subscriptions/cancel` - Cancel

**Deployments**
- `GET /api/deployments/` - List deployments
- `POST /api/deployments/` - Create deployment
- `POST /api/deployments/validate-license` - Validate key

### Console Backend (Port 4010)

**Chat**
- `WS /api/ws/chat` - Real-time chat (WebSocket)
- `POST /api/chat` - Single message

**Data**
- `GET /api/data/tables` - List Delta Lake tables
- `GET /api/data/query` - Query data (SQL)
- `GET /api/data/search` - Vector search

**Ingestion**
- `POST /api/ingest/trigger` - Trigger ingestion
- `GET /api/ingest/status/{job_id}` - Check status

**MCPs**
- `GET /api/mcps/list` - List available MCPs
- `POST /api/mcps/install` - Install MCP
- `GET /api/mcps/{name}/info` - MCP info

---

## 📤 File Upload & Data Ingestion

### Upload Endpoints Overview

The platform provides **3 upload endpoints** for different use cases:

#### 1. Synchronous Upload (Most Common)
**Endpoint**: `POST /api/upload/files`
**Implementation**: `api/routes/upload.py:146`

```bash
curl -X POST "http://localhost:4080/api/upload/files?customer_id=eaton&selected_mcps=ctax,law,etim" \
  -F "files=@product_catalog.csv" \
  -F "files=@technical_specs.pdf" \
  -F "files=@contracts.docx"
```

**Behavior**:
- Uploads files to MinIO immediately
- Returns after upload completes
- Triggers ingestion in background via FastAPI BackgroundTasks
- **First upload detection**: If bucket doesn't exist → triggers full customer deployment

**Response**:
```json
{
  "success": true,
  "message": "3 files uploaded. Ingestion started in background.",
  "files": [
    {
      "filename": "product_catalog.csv",
      "size": 245760,
      "path": "s3://customer-eaton/20251128_103000_product_catalog.csv",
      "bucket": "customer-eaton"
    }
  ],
  "ingestion_triggered": true,
  "selected_mcps": ["ctax", "law", "etim"],
  "installation_triggered": true  // Only on first upload
}
```

#### 2. Async Upload (For Large Batches)
**Endpoint**: `POST /api/upload-async/start`
**Implementation**: `api/routes/upload_async.py:133`

```bash
# Start upload
curl -X POST "http://localhost:4080/api/upload-async/start?customer_id=eaton" \
  -F "files=@large_file1.pdf" \
  -F "files=@large_file2.pdf"

# Returns immediately with job_id
{
  "success": true,
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_files": 2
}

# Poll for status
curl http://localhost:4080/api/upload-async/status/550e8400-e29b-41d4-a716-446655440000

{
  "job_id": "550e8400-...",
  "status": "uploading",  // queued, uploading, completed, failed
  "progress": 45,
  "uploaded_count": 1,
  "current_file": "large_file1.pdf"
}
```

#### 3. Onboarding Upload (Legacy)
**Endpoint**: `POST /api/onboarding/data-sources`
**Implementation**: `api/routes/onboarding.py:87`

Used by onboarding wizard frontend.

### First Upload Detection & Deployment

**What happens on first file upload**:

`api/routes/upload.py:166-257`:
```python
# Check if bucket exists
customer_bucket = f"customer-{customer_id}"
if not minio.bucket_exists(customer_bucket):
    # FIRST UPLOAD DETECTED! 🚀
    minio.make_bucket(customer_bucket)

    # Trigger deployment orchestrator
    orchestrator = CustomerDeploymentOrchestrator()
    deployment_info = await orchestrator.deploy_customer(
        customer_id=customer_id,
        company_name=f"Customer {customer_id}",
        selected_mcps=["ctax", "law", "etim"],
        uploaded_files_bucket=customer_bucket,
        deployment_type="managed"
    )

    # Provisions (3 containers per customer):
    # - Dedicated Mixtral instance (vLLM with customer LoRA)
    # - Embeddings service (multilingual-e5-large, CPU)
    # - Lakehouse service (Delta Lake + LanceDB HTTP API)
    #
    # MCPs are NOT deployed - accessed as shared services
    # Customer gets database flag: enabled_mcps = {"etim": true}
```

**Deployment timeline** (with pre-built images):
- MinIO upload: ~10 seconds (depends on file size)
- Docker container start: ~30 seconds (images ready, no downloads)
- vLLM load Mixtral: ~2-5 minutes (if not pre-downloaded in image)
- Ingestion pipeline: ~2-10 minutes (depends on data volume)
- **Total**: ~3-6 minutes for complete deployment (vs 15+ min before)

### MinIO Bucket Structure

**Per-customer isolation**:
```
MinIO (localhost:4050)
├── customer-eaton/
│   ├── 20251128_103000_product_catalog.csv
│   ├── 20251128_103001_technical_specs.pdf
│   ├── 20251128_103002_contracts.docx
│   ├── 20251128_103010_unknown_format.dat  # Claude generates handler!
│   └── raw/                                 # Original uploads
│
├── customer-eprocat/
│   ├── 20251128_104500_catalog.xml
│   └── ...
│
└── uploads/                                 # Default bucket (dev)
```

**Bucket naming**: `customer-{customer_id}`
**File naming**: `{timestamp}_{original_filename}`
**Access**: Each customer can only access their own bucket

### Ingestion Pipeline Trigger

After files are uploaded to MinIO, ingestion runs automatically:

`api/routes/upload.py:45-143`:
```python
async def trigger_ingestion(customer_id: str, bucket_name: str, selected_mcps: List[str]):
    """Background task: Downloads from MinIO and runs ingestion"""

    # 1. Download files from MinIO to temp directory
    temp_dir = Path(f"/tmp/ingestion_{customer_id}_")
    for obj in minio.list_objects(bucket_name):
        minio.fget_object(bucket_name, obj.object_name, temp_dir / obj.object_name)

    # 2. Run ingestion orchestrator
    orchestrator = IngestionOrchestrator(
        lakehouse_path=Path(f"/tmp/lakehouse/{customer_id}"),
        vllm_url="http://localhost:4030",
        embedding_model="intfloat/multilingual-e5-large"
    )

    # 3. Process: Crawl → Extract → Classify → Chunk → Embed → Load
    result = await orchestrator.ingest(folder_configs)

    # 4. Cleanup temp files
    shutil.rmtree(temp_dir)
```

### Claude-Powered Adaptive Handlers

**The Killer Feature**: When encountering unknown file formats, Claude generates handlers automatically.

**Implementation**: `ingestion/claude_handler_generator.py:39`

**Example: EATON uploads proprietary `.DAT` file**

```python
# 1. FileCrawler detects unknown extension
file = Path("eaton_products.dat")
if not has_handler(file.extension):
    # 2. Analyze file structure
    analysis = analyze_file_structure(file)
    # Reads first 4KB, detects:
    # - Encoding (UTF-8, ISO-8859-1, etc.)
    # - Structure (CSV, XML, JSON, fixed-width)
    # - Domain hints (DATEV, SAP, etc.)

    # 3. Prompt Claude Sonnet 4.5
    prompt = f"""
    Generate a Python handler class to extract data from this file:

    File: {file.name}
    Extension: {file.suffix}
    Encoding: {analysis['encoding']}
    Sample: {analysis['sample_text']}

    Requirements:
    - Inherit from BaseHandler
    - Implement async extract(path: Path) -> str
    - Return extracted text content
    """

    # 4. Claude generates handler code
    handler_code = claude.generate(prompt)

    # 5. Validate with AST parsing
    ast.parse(handler_code)  # Syntax check

    # 6. Test on sample file
    handler = load_handler(handler_code)
    result = await handler.extract(file)

    # 7. Register for future use
    register_handler(".dat", handler)
```

**Generated handler example**:
```python
class EatonDatHandler(BaseHandler):
    """Auto-generated handler for EATON .DAT files"""

    async def extract(self, path: Path) -> Optional[str]:
        """Extract tab-delimited product data"""
        try:
            with open(path, 'r', encoding='iso-8859-1') as f:
                lines = f.readlines()

            # Parse header
            header = lines[0].strip().split('\t')

            # Extract records
            records = []
            for line in lines[1:]:
                values = line.strip().split('\t')
                record = dict(zip(header, values))
                records.append(record)

            # Convert to text for RAG
            text = "\n".join([
                f"Product {r['id']}: {r['name']} - {r['description']}"
                for r in records
            ])

            return text
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return None
```

**Key files**:
- `ingestion/claude_handler_generator.py:39` - Generator implementation
- `ingestion/crawler/file_crawler.py:220` - Handler invocation
- `ingestion/crawler/file_handlers/` - Built-in handlers (PDF, DOCX, CSV, XML, etc.)

### Complete Ingestion Flow

**Full pipeline**: `ingestion/orchestrator.py:167`

```
1. CRAWL (FileCrawler)
   ├─ Scan folders recursively
   ├─ Detect file types
   └─ Generate handlers for unknown formats (Claude)

2. EXTRACT (FileHandlers)
   ├─ PDF → pypdf2
   ├─ DOCX → python-docx
   ├─ CSV → pandas
   ├─ XML → lxml
   └─ .DAT → Claude-generated handler

3. CLASSIFY (DocumentClassifier)
   ├─ Analyze content with vLLM/Claude
   ├─ Route to appropriate MCP:
   │   ├─ Tax documents → CTAX
   │   ├─ Contracts → LAW
   │   ├─ Product data → ETIM
   │   └─ General → General MCP

4. PROCESS (Chunker)
   ├─ Structure-aware chunking
   ├─ Preserve context (paragraphs, tables, lists)
   └─ Extract entities (companies, dates, amounts)

5. EMBED (Embedder)
   ├─ Model: intfloat/multilingual-e5-large
   ├─ Batch size: 128
   └─ Output: 1024-dim vectors

6. LOAD (Lakehouse)
   ├─ Delta Lake: Structured tables (documents, chunks, entities)
   ├─ LanceDB: Vector embeddings for semantic search
   └─ Neo4j: Entity relationships (planned)
```

**Progress tracking**: Real-time callbacks via `orchestrator.on_progress(callback)`

### Testing Upload & Ingestion

**Sample test data**: `tests/fixtures/sample_data/`

```bash
# Test with sample unknown format
curl -X POST "http://localhost:4080/api/upload/files?customer_id=test" \
  -F "files=@tests/fixtures/sample_data/sample_unknown.dat"

# Expected: Claude generates handler automatically

# Check ingestion status
curl http://localhost:4080/api/upload/list

# Verify deployment
curl http://localhost:4080/api/onboarding/verify/test
```

**E2E test**: `tests/e2e/test_complete_onboarding_flow.py`

```bash
# Run full onboarding test (includes upload + deployment)
pytest tests/e2e/test_complete_onboarding_flow.py -v
```

---

## 🐳 Docker Images & Deployment

### Production-Ready Images

All images are **pre-built with dependencies** for instant deployment to new customers:

| Image | Size | Contains | Build Time |
|-------|------|----------|------------|
| `0711-os-embeddings:latest` | 9.95GB | multilingual-e5-large (pre-downloaded) | ~30 sec |
| `0711/lakehouse:latest` | 802MB | Delta Lake + LanceDB + FastAPI | ~25 sec |
| `0711/platform:latest` | 716MB | Control Plane API (FastAPI, Stripe) | ~40 sec |
| `vllm/vllm-openai:latest` | 28.8GB | vLLM inference engine | Pull from registry |

**Key benefit**: Models are pre-downloaded, so containers start instantly without download delays.

### Building All Images

**Automated build script**:
```bash
cd /home/christoph.bertsch/0711/0711-OS

# Build all images (takes ~2 minutes)
./scripts/build_all_images.sh

# Optional: Build with pre-downloaded Mixtral (takes ~30 min, saves time on deployments)
./scripts/build_all_images.sh --with-vllm
```

**What gets built**:
1. **Embeddings service** - multilingual-e5-large model baked in
2. **Lakehouse service** - Delta Lake + LanceDB with HTTP API
3. **Platform API** - Control Plane (customer mgmt, billing)
4. **vLLM** (optional) - Mixtral 8x7B pre-downloaded

### Deploying a New Customer

**Step 1: Customer uploads files**
```bash
curl -X POST "http://localhost:4080/api/upload/files?customer_id=new-customer" \
  -F "files=@data.csv"
```

**Step 2: System auto-generates deployment**
```bash
# Automatically created at:
/home/christoph.bertsch/0711/deployments/new-customer/docker-compose.yml
```

**Step 3: Start customer stack**
```bash
cd /home/christoph.bertsch/0711/deployments/new-customer
docker compose up -d

# Result (in <2 minutes):
# ✅ new-customer-vllm (loading Mixtral)
# ✅ new-customer-embeddings (ready instantly)
# ✅ new-customer-lakehouse (ready instantly)
```

**Step 4: Enable MCPs for customer**
```bash
# Via API (no deployment needed)
curl -X POST http://localhost:4080/api/mcp-services/enable/etim \
  -H "Authorization: Bearer $CUSTOMER_TOKEN"

# Customer can now use ETIM MCP (shared service)
```

### EATON Reference Implementation

**Location**: `/home/christoph.bertsch/0711/deployments/eaton/`

**Status**: ✅ **Live and working**
- vLLM: Loading Mixtral on H200 GPU 1
- Lakehouse: Serving 31,807 vectors via HTTP (port 9302)
- Embeddings: Ready with pre-downloaded model (port 9301)
- ETIM MCP: Enabled and accessible

**Test lakehouse**:
```bash
# Health check
curl http://localhost:9302/health

# Stats
curl http://localhost:9302/stats

# Query documents
curl "http://localhost:9302/delta/query/general_documents?limit=5"

# List Lance datasets
curl http://localhost:9302/lance/datasets
```

### Shared MCP Services

**Available MCPs** (not deployed per-customer):

1. **ETIM MCP** (port 7779)
   - Product classification (ETIM/ECLASS)
   - Location: `/home/christoph.bertsch/0711/0711-etim-mcp/`
   - Customers: Enable via API, access via MCP Router
   - Update: Independent roadmap, updates propagate to all customers

**Enable MCP for customer**:
```bash
# List available MCPs
GET /api/mcp-services/available

# Enable for customer (updates database flag)
POST /api/mcp-services/enable/etim

# Query MCP with customer context
POST /api/mcp-services/query
{
  "mcp_name": "etim",
  "query": "Classify products in catalog",
  "context": {}
}
```

**MCP routing** (`orchestrator/mcp/mcp_router.py`):
- Adds customer_id to all requests
- Ensures lakehouse_path points to customer data
- Enforces access control (checks enabled_mcps)

---

## 🔐 Authentication & Security

### JWT Tokens
- **Algorithm**: HS256
- **Expiration**: 7 days (configurable)
- **Claims**: customer_id, email, tier

### Environment Variables
- `JWT_SECRET` - Secret key for JWT signing
- `STRIPE_SECRET_KEY` - Stripe API key
- `STRIPE_WEBHOOK_SECRET` - Webhook validation
- `HF_TOKEN` - Hugging Face token (for Mixtral)
- `DATABASE_URL` - PostgreSQL connection
- `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` - Object storage

### DSGVO/GDPR Compliance
- Audit logging in `audit_log` table
- Data export endpoint: `GET /api/customer/export-data`
- Data deletion: `DELETE /api/customer/delete-account`

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=ingestion --cov=lakehouse --cov=mcps --cov-report=html

# Run specific test file
pytest tests/unit/test_ingestion.py

# Run integration tests (requires Docker)
pytest tests/integration/

# Run E2E tests (requires full stack)
pytest tests/e2e/
```

---

## 📝 Development Guidelines

### Code Style
- **Python**: Black (line length 100) + Ruff linting
- **TypeScript**: ESLint + Prettier
- **Imports**: Absolute imports preferred

### Git Workflow
- **Main branch**: `main` (protected)
- **Feature branches**: `feature/name`
- **Bug fixes**: `fix/name`
- **Commit format**: `type(scope): description`

### Adding New MCPs
1. Create file in `mcps/core/` or `mcps/marketplace/`
2. Inherit from `BaseMCP` (`mcps/sdk/base_mcp.py`)
3. Use `@tool` decorator for callable functions
4. Use `@resource` decorator for data sources
5. Register in `mcps/registry.py`

Example:
```python
# mcps/core/ecommerce.py
from mcps.sdk import BaseMCP, tool

class EcommerceMCP(BaseMCP):
    name = "ecommerce"
    description = "E-commerce analytics specialist"

    @tool
    async def analyze_sales(self, period: str):
        """Analyze sales for given period"""
        docs = await self.lakehouse.search(f"sales {period}")
        return await self.llm.query(docs, "Analyze sales trends")
```

---

## 🐛 Common Issues & Solutions

### Issue: vLLM won't start (GPU)
**Solution**: Check GPU memory with `nvidia-smi`. Mixtral 8x7B needs 24GB+.

### Issue: Embeddings service failing
**Solution**: Check HF_TOKEN is set in .env. Model downloads from Hugging Face.

### Issue: MinIO bucket not found
**Solution**: Run `docker exec 0711-minio mc mb /data/customer-eaton`

### Issue: PostgreSQL connection refused
**Solution**: Check PostgreSQL is running: `docker ps | grep 0711-postgres`

### Issue: Frontend can't connect to backend
**Solution**: Check CORS_ORIGINS in .env includes `http://localhost:4020`

---

## 📚 Key Documentation Files

- `README.md` - Quick overview + getting started
- `ARCHITECTURE_COMPLETE.md` - Deep dive into architecture
- `DEPLOYMENT.md` - Production deployment guide
- `QUICKSTART.md` - Fast setup for development
- `MARKETING.md` - Marketing strategy, messaging, and personas
- `.env.example` - All environment variables

---

## 🌐 Marketing Website & Positioning

### Brand Positioning
**"Built For Builders, Not Bureaucrats"**

The 0711 platform targets three primary personas with distinct pain points and value propositions:

#### 1. **Founders** (Primary Persona)
**Pain Points:**
- Spending 60% of time managing vendors instead of building product
- Burning runway on consultants (€2,500/day) and tool sprawl
- Can't compete with enterprise competitors due to infrastructure gap

**Value Propositions:**
- **Back to Building**: Stop managing software, get back to what matters
- **Day-One Infrastructure**: Enterprise capabilities without enterprise complexity
- **Capital Efficiency**: Stop burning runway, invest in growth
- **Compete With Giants**: 20 people with 0711 > 200 people with legacy

**Key Message:** *"You didn't start a company to manage vendors."*

#### 2. **CEOs** (Secondary Persona)
**Pain Points:**
- Board pressure for growth/margins, not ERP migration timelines
- Can't get business answers without 3-week report cycles
- 70% of OpEx goes to "keeping the lights on"

**Value Propositions:**
- **Instant Clarity**: Ask anything, get answers in seconds
- **70% Cost Reduction**: Eliminate consultant layer, tool sprawl
- **10x Decision Speed**: No more waiting for reports
- **M&A Ready**: Integrate acquisitions in days, not years

**Success Metrics:** 90 days to positive ROI, €3-8M annual savings

#### 3. **CTOs & Dev Gods** (Technical Influencer)
**Pain Points:**
- Tired of cleaning up after enterprise vendors
- Vendor lock-in makes migrations impossible
- Explaining to leadership why "simple" integrations take 6 months

**Value Propositions:**
- **Real Architecture**: Unified Lakehouse, Ray, vLLM, DSPy (not slides)
- **Local-First LLM**: Your data never leaves, Mixtral + LoRA hot-swapping
- **MCP SDK**: Build custom capabilities in Python, your rules
- **No Vendor Lock-In**: Open standards, portable data

**Key Message:** *"Finally, infrastructure that doesn't insult your intelligence."*

### Website Structure

**Homepage** (`apps/website/app/page.tsx`):
- Hero: "One brain. Zero friction."
- Manifesto: Why enterprise software is fundamentally broken
- How It Works: 4-step process (talk → learn → act → win)
- Features: 7 engines (Product, Pricing, Finance, Marketing, Research, Operations)
- Results: 10x speed, 70% cost reduction, 1 day deploy, 0 meetings

**Builders Page** (`apps/website/app/builders/page.tsx`):
- Hero: "For the ones who actually build things"
- **Founders Section**: 4 key value props + testimonial quote
- **CEOs Section**: 4 key value props + ROI stats (90 days, €3-8M savings)
- **CTOs Section**: 4 technical value props + credibility quote
- **Law MCP Showcase**: Deep-dive into one MCP (contract review, €3k/mo vs €50k/mo)
- **Liberation Section**: "The Bloodsuckers" satire (6 villains we replace)
  - Management Consultants (€2,500/day → €2,500/month)
  - Corporate Lawyers (€500/hour → 95% automated)
  - Tax Advisors (€400/hour → CTAX Engine)
  - External Auditors (€350/hour → continuous audit)
  - Middle Management (€120k/year → nothing, that's the point)
  - ERP Implementation (€15M/project → 1 day install)

**Pricing Page** (`apps/website/app/pricing/`):
- Transparent, value-based pricing
- Small business (5-20 employees): €5,000/month
- Mid-market (20-200 employees): €15,000/month
- Enterprise (200+ employees): Custom
- Self-hosted: One-time license + support

### Voice & Tone Guidelines

**What We Say:**
- "Installs in one day. Not one year."
- "70% cost reduction. Not 7%."
- "Built for builders, not bureaucrats."
- "Actually works" (when describing software)

**What We Don't Say:**
- "Best-in-class solution"
- "Synergistic ecosystem"
- "Digital transformation journey"
- "Paradigm shift"

**Writing Rules:**
1. Active voice always
2. Specific numbers (70% not "significant")
3. No jargon unless technical
4. Short sentences, one idea each
5. Proof over promises (show, don't tell)

### The "Bloodsuckers" Framework
Satirical positioning identifying consultants/middlemen who extract value without creating it. Always prefaced with "⚠ Satire Warning ⚠". Resonates with persona frustration while demonstrating concrete alternatives.

**Key Quote:** *"The best part of 0711 isn't what it does. It's who it fires."*

### Marketing Documentation
See `MARKETING.md` for complete:
- Persona psychographic profiles
- Content pillars and calendar
- Competitive differentiation
- Go-to-market strategy
- Messaging framework

---

## 🎓 Customer Journey

### Managed (SaaS)
1. Visit 0711.cloud/onboarding
2. Upload data files
3. Select MCPs (CTAX, LAW, ETIM, etc.)
4. Wait 10 minutes (deployment + ingestion)
5. Access console at {customer}.0711.cloud
6. Chat with AI brain

### Self-Hosted (On-Premise)
1. Download installer: `install-0711.sh`
2. Run: `sudo ./install-0711.sh --license=ENTERPRISE-KEY`
3. Select data folders
4. Wait 15 minutes (Docker pull + ingestion)
5. Access at http://localhost:3000
6. Chat with AI brain

---

## 🚧 Implementation Status

### ✅ Completed
- [x] Control Plane API (auth, subscriptions, licensing)
- [x] Console Backend + Frontend
- [x] Ingestion pipeline (crawler, handlers, classifier)
- [x] Claude-powered handler generation
- [x] Lakehouse (Delta Lake + LanceDB)
- [x] MCP SDK + core MCPs (CTAX, LAW, TENDER)
- [x] LoRA manager (hot-swap code)
- [x] Model manager (LRU eviction)
- [x] MinIO file storage
- [x] Onboarding wizard
- [x] WebSocket chat

### ⚠️ Partially Implemented
- [~] vLLM deployment (Dockerfile ready, not integrated)
- [~] Per-customer deployment orchestration (code exists, not wired)
- [~] Ray Serve MCP orchestration (planned)

### ❌ Missing
- [ ] LoRA training pipeline (continuous learning)
- [ ] Graph database integration (Neo4j)
- [ ] Self-hosted installer package
- [ ] Kubernetes manifests
- [ ] CI/CD pipeline

---

## 🔧 Working with Claude Code

### Common Tasks

**Start the platform**:
```bash
./START_ALL.sh
```

**Stop everything**:
```bash
./STOP_ALL.sh
```

**Add a new file handler**:
1. Create `ingestion/crawler/file_handlers/new_format.py`
2. Inherit from `BaseFileHandler`
3. Implement `extract()` method
4. Register in `__init__.py`

**Add a new API route**:
1. Create `api/routes/new_feature.py` or `console/backend/routes/new_feature.py`
2. Define FastAPI router
3. Import in `main.py`
4. Include router: `app.include_router(new_feature.router)`

**Query the lakehouse**:
```python
from lakehouse.vector.lance_store import LanceStore

store = LanceStore(path="/data/lakehouse/lance")
results = await store.search("tax documents 2024", limit=10)
```

**Test MCP locally**:
```python
from mcps.core.ctax import CTaxMCP

mcp = CTaxMCP(lakehouse=lakehouse, llm=llm_client)
result = await mcp.calculate_tax_liability(year=2024, revenue=1_000_000)
```

### File Naming Conventions
- Python modules: `snake_case.py`
- Classes: `PascalCase`
- Functions: `snake_case()`
- Constants: `UPPER_SNAKE_CASE`
- Components (React): `PascalCase.tsx`

---

## 💬 Contact & Support

- **Engineering Team**: engineering@0711.ai
- **Documentation**: https://docs.0711.io (planned)
- **GitHub**: Internal repository

---

**This is a defensive security tool for enterprise data management. All data processing respects DSGVO/GDPR compliance.**
