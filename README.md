# 0711 Intelligence Platform

> Enterprise AI Operating System with per-customer isolated AI instances, adaptive data ingestion, and domain-specific MCP experts.

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![TypeScript](https://img.shields.io/badge/typescript-5.0+-blue.svg)](https://www.typescriptlang.org/)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)

---

## ⚡ Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker + Docker Compose
- PostgreSQL 15+
- Redis 7+
- (Optional) NVIDIA GPU for model inference

### Installation

```bash
# 1. Clone repository
git clone https://github.com/YOUR_ORG/0711-OS.git
cd 0711-OS

# 2. Set up environment
cp .env.example .env
# Edit .env with your API keys (see .env.example for all required keys)

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install frontend dependencies
cd console/frontend && npm install && cd ../..
cd apps/website && npm install && cd ../..

# 5. Start infrastructure
docker compose up -d postgres redis minio embeddings

# 6. Run database migrations
alembic upgrade head

# 7. Start all services
./START_ALL.sh
```

**Access Points:**
- **Console (Chat)**: http://localhost:4020
- **Control Plane API**: http://localhost:4080
- **API Docs**: http://localhost:4080/docs
- **Marketing Website**: http://localhost:4000
- **MinIO Console**: http://localhost:4051

---

## 🏗️ Architecture

```
Customer Data (MinIO)
    ↓
Adaptive Ingestion (Claude-generated handlers)
    ↓
Lakehouse (Delta Lake + LanceDB)
    ↓
MCP Router (CTAX, LAW, ETIM specialists)
    ↓
Mixtral 8x7B + Customer LoRA
```

### Key Features

- **Per-Customer AI**: Isolated Mixtral 8x7B instances with hot-swappable LoRA adapters (<1s swap time)
- **Adaptive Ingestion**: Claude Sonnet 4.5 generates handlers for unknown file formats on-the-fly
- **Full RAG Stack**: Delta Lake (structured) + LanceDB (vectors) + Neo4j (graph, planned)
- **MCP System**: Domain-specific AI experts (corporate tax, legal contracts, procurement)
- **Two Deployment Modes**: Managed SaaS + Self-hosted on-premise
- **DSGVO Compliant**: Complete data isolation, audit logging, privacy by design

### Technology Stack

**Backend:**
- FastAPI (Control Plane + Console Backend)
- SQLAlchemy + PostgreSQL
- Redis (caching + pub/sub)
- Pydantic (validation)

**Frontend:**
- Next.js 14 (App Router)
- React 18 + TypeScript
- Tailwind CSS
- WebSocket (real-time chat)

**AI/ML:**
- vLLM (Mixtral 8x7B-Instruct)
- LoRA (fine-tuning)
- sentence-transformers (multilingual-e5-large)
- Claude Sonnet 4.5 (adaptive handlers)

**Lakehouse:**
- Delta Lake (ACID transactions)
- LanceDB (columnar vectors)
- MinIO (S3-compatible storage)
- Neo4j (graph, planned)

---

## 📁 Project Structure

```
0711-OS/
├── api/                    # Control Plane API (customer mgmt, billing, auth)
│   ├── models/            # SQLAlchemy models
│   ├── routes/            # FastAPI endpoints
│   └── services/          # Business logic (Stripe, email, etc.)
├── console/               # Customer-facing console
│   ├── backend/          # Console API + WebSocket
│   └── frontend/         # Next.js chat interface
├── ingestion/             # Data ingestion pipeline
│   ├── crawler/          # File crawlers + handlers
│   ├── classifier/       # Document classification
│   ├── processor/        # Chunking + embedding
│   └── loader/           # Load to lakehouse
├── lakehouse/             # Multi-modal data storage
│   ├── delta/            # Delta Lake tables
│   ├── vector/           # LanceDB vector store
│   └── storage/          # MinIO integration
├── inference/             # Model serving
│   ├── server.py         # vLLM wrapper
│   └── lora_manager.py   # LoRA hot-swapping
├── mcps/                  # Model Context Protocol system
│   ├── sdk/              # BaseMCP + decorators
│   └── core/             # CTAX, LAW, TENDER experts
├── orchestrator/          # MCP routing + workflows
│   └── mcp/              # Model manager + router
├── provisioning/          # Deployment automation
│   ├── api/              # Provisioning API
│   └── installer/        # Self-hosted installer
├── tests/                 # Test suite
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── apps/                  # Public websites
│   ├── website/          # Marketing site
│   └── admin/            # Admin dashboard
└── docs/                  # Documentation
```

---

## 🧪 Development

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test suite
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/e2e/ -v

# Run with coverage
pytest --cov=api --cov=ingestion --cov=lakehouse --cov-report=html
```

### Code Formatting

```bash
# Format Python code
black . --line-length 100
ruff check --fix .

# Format TypeScript
cd console/frontend && npm run lint
cd apps/website && npm run lint
```

### Building Docker Images

```bash
# Build all platform images
./scripts/build_all_images.sh

# Build with vLLM (optional, large download)
./scripts/build_all_images.sh --with-vllm
```

### Running in Development

```bash
# Start infrastructure only
docker compose up -d postgres redis minio

# Run services individually (for debugging)
cd api && uvicorn main:app --reload --port 4080
cd console/backend && uvicorn main:app --reload --port 4010
cd console/frontend && npm run dev
cd apps/website && npm run dev
```

---

## 🚀 Deployment

### Managed SaaS Deployment

For managed deployments, customer instances are automatically provisioned when they upload their first files:

```bash
# Customer uploads trigger deployment
POST /api/upload/files?customer_id=acme

# System automatically provisions:
# - Dedicated Mixtral instance (vLLM with customer LoRA)
# - Embeddings service (multilingual-e5-large, CPU)
# - Lakehouse service (Delta Lake + LanceDB HTTP API)
```

See [Deployment Guide](docs/deployment/README.md) for details.

### Self-Hosted Installation

```bash
# Download installer
wget https://install.0711.io/install-0711.sh

# Run installation
sudo ./install-0711.sh --license=YOUR-LICENSE-KEY

# Access at http://localhost:3000
```

---

## 📚 Documentation

- **[Architecture Overview](docs/architecture/README.md)** - System design and data flow
- **[Developer Reference (CLAUDE.md)](docs/reference/CLAUDE.md)** - Complete technical context for AI assistants
- **[API Documentation](docs/api/README.md)** - API endpoints and usage
- **[Deployment Guide](docs/deployment/README.md)** - Production deployment instructions
- **[Contributing Guidelines](CONTRIBUTING.md)** - How to contribute
- **[Security Policy](SECURITY.md)** - Security practices and reporting

---

## 🔐 Security

### Reporting Vulnerabilities

**DO NOT open public issues for security vulnerabilities.**

Email: [security@0711.io](mailto:security@0711.io)

See [Security Policy](SECURITY.md) for details.

### Security Features

- All secrets stored in `.env` (never committed)
- JWT authentication with 7-day expiration
- DSGVO/GDPR compliance for customer data
- Per-customer data isolation (separate buckets, lakehouses, models)
- Audit logging for all critical operations
- Role-based access control (RBAC)

---

## 📄 License

**Proprietary License**

Copyright © 2025 0711 Team. All rights reserved.

Unauthorized copying, distribution, or use prohibited.

See [LICENSE](LICENSE) for full terms.

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make changes with tests
4. Format code: `black . && ruff check --fix .`
5. Run tests: `pytest tests/ -v`
6. Commit: `git commit -m "feat: add feature"`
7. Push and create Pull Request

---

## 🌟 Key Innovations

### 1. Claude-Powered Adaptive Ingestion

When encountering unknown file formats, the platform uses Claude Sonnet 4.5 to analyze the file structure and generate a Python handler class automatically:

```python
# Customer uploads proprietary .DAT file
→ Claude analyzes structure
→ Generates handler class
→ Validates with AST parsing
→ Tests on sample data
→ Registers for future use
```

**Result**: Support for ANY file format without manual coding.

### 2. Hot-Swappable LoRA Adapters

Each customer gets their own fine-tuned model (LoRA adapter) that can be swapped in <1 second:

```python
# Customer A query → Load customer_a.safetensors
# Customer B query → Load customer_b.safetensors
# LRU eviction when GPU memory full
```

**Result**: Personalized AI for every customer without deploying separate model servers.

### 3. Shared MCP Architecture

Domain experts (CTAX, LAW, ETIM) are deployed once and shared across all customers:

```
Per-customer: vLLM + Embeddings + Lakehouse (3 containers)
Shared: MCPs accessed via MCP Router
```

**Result**: 60% fewer containers, faster deployments, easier updates.

---

## 📊 System Requirements

### Development

- **CPU**: 4+ cores
- **RAM**: 16GB+
- **Storage**: 50GB+ SSD

### Production (Managed)

- **CPU**: 16+ cores
- **RAM**: 64GB+
- **GPU**: NVIDIA A100 80GB (or H100) for vLLM
- **Storage**: 500GB+ NVMe SSD

### Production (Self-Hosted)

- **Minimum**: 8 cores, 32GB RAM, 100GB SSD
- **Recommended**: 16 cores, 64GB RAM, 500GB SSD, NVIDIA GPU

---

## 🆘 Support

- **Documentation**: https://docs.0711.io (planned)
- **Email**: support@0711.io
- **GitHub Issues**: For bug reports and feature requests

---

## 🙏 Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [vLLM](https://github.com/vllm-project/vllm) - High-performance LLM serving
- [Delta Lake](https://delta.io/) - ACID transactions on data lake
- [LanceDB](https://lancedb.com/) - Columnar vector database
- [Anthropic Claude](https://www.anthropic.com/) - Adaptive handler generation

---

**Built for Builders, Not Bureaucrats** 🚀
