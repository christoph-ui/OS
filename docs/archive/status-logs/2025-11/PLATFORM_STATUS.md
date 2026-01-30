# 0711 Platform - Complete Status

**Last Updated**: 2025-11-25

---

## ✅ ALL SYSTEMS RUNNING (40XX Ports)

### 🌐 Frontend Applications

| Service | Port | URL | Status |
|---------|------|-----|--------|
| **Marketing Website** | 4000 | http://localhost:4000 | ✅ RUNNING |
| **Onboarding Flow** | 4000 | http://localhost:4000/onboarding | ✅ RUNNING |
| **Admin Mockup** | 4000 | http://localhost:4000/admin | ✅ RUNNING |
| **Console UI** | 4020 | http://localhost:4020 | ✅ RUNNING |

### ⚙️ Backend APIs

| Service | Port | URL | Docs | Status |
|---------|------|-----|------|--------|
| **Control Plane API** | 4080 | http://localhost:4080 | http://localhost:4080/docs | ✅ RUNNING |
| **Console Backend** | 4010 | http://localhost:4010 | http://localhost:4010/docs | ✅ RUNNING |

### 💾 Infrastructure

| Service | Port | Access | Status |
|---------|------|--------|--------|
| **PostgreSQL** | 4005 | localhost:4005 | ✅ RUNNING |
| **Redis** | 6379 | localhost:6379 (existing) | ✅ RUNNING |

### 🤖 AI/ML Services (Docker Compose)

| Service | Port | Status | Notes |
|---------|------|--------|-------|
| **vLLM** | 4030 | 🔧 Not Started | Optional - run with `docker compose --profile gpu up vllm` |
| **Embeddings** | 4040 | 🔧 Not Started | Optional |
| **MinIO** | 4050/4051 | 🔧 Not Started | Optional - run with `docker compose up minio` |

---

## 🚀 Quick Start

### Start Everything
```bash
cd /home/christoph.bertsch/0711/0711-OS
./START_ALL.sh
```

### Stop Everything
```bash
./STOP_ALL.sh
```

---

## 🔌 SSH Tunnel Configuration

**Add these ports to your SSH tunnel from Mac:**

```bash
ssh -L 4000:localhost:4000 \
    -L 4010:localhost:4010 \
    -L 4020:localhost:4020 \
    -L 4080:localhost:4080 \
    -L 4005:localhost:4005 \
    -L 9010:localhost:9010 \
    -L 9011:localhost:9011 \
    ... (your other ports) \
    christoph.bertsch@192.168.145.10 -N
```

---

## 📍 What Each Service Does

### 1. **Marketing Website** (Port 4000)
- Landing page
- Onboarding wizard (7 steps)
- Basic admin mockup
- **Tech**: Next.js 14, React, TypeScript

### 2. **Control Plane API** (Port 4080)
- Customer management
- Billing & subscriptions
- Deployment management
- Onboarding API endpoints
- **Tech**: FastAPI, SQLAlchemy, PostgreSQL

### 3. **Console Backend** (Port 4010)
- WebSocket chat interface
- MCP runtime management
- Data browsing (lakehouse queries)
- Ingestion job management
- **Tech**: FastAPI, WebSocket, Platform core

### 4. **Console Frontend** (Port 4020)
- Chat with your data using MCPs
- Data browser UI
- Ingestion panel
- MCP manager
- **Tech**: Next.js 14, React, Tailwind CSS, Anthropic design

---

## 🔑 Demo User Credentials

**Console Access:**
- Email: `admin@0711.io`
- Password: `admin123`
- Role: Admin

**Testing:**
- Email: `test@example.com`
- Password: `test123`
- Role: User

---

## 📊 Platform Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    0711 PLATFORM                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Marketing   │  │   Admin      │  │   Console    │      │
│  │  (Port 4000) │  │  (Port 4000) │  │ (Port 4020)  │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                 │              │
│         ▼                 ▼                 ▼              │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │ Control Plane│  │   Console    │                        │
│  │  API (4080)  │  │  Backend     │                        │
│  └──────┬───────┘  │   (4010)     │                        │
│         │          └──────┬───────┘                        │
│         │                 │                                │
│         ▼                 ▼                                │
│  ┌──────────────────────────────────────┐                  │
│  │  PostgreSQL (4005) │ Redis (6379)    │                  │
│  └──────────────────────────────────────┘                  │
│                         │                                  │
│                         ▼                                  │
│         ┌───────────────────────────────┐                  │
│         │  Lakehouse (Delta + Lance)    │                  │
│         │  MCPs (CTAX, LAW, ETIM, etc.) │                  │
│         └───────────────────────────────┘                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Key Features Implemented

### ✅ **Onboarding System**
- 7-step wizard (Welcome → Company → Data → MCPs → Connectors → Deploy → Complete)
- Real-time pricing calculation
- MCP selection (12+ available)
- Connector configuration
- Backend API integration

### ✅ **Control Plane**
- Customer/company management
- Subscription handling
- Deployment tracking
- License key generation
- German invoice support (planned)

### ✅ **Console**
- Chat interface with MCPs
- Data browser
- Ingestion management
- MCP runtime status
- WebSocket real-time communication

### ✅ **Integration Layer**
- TypeScript client for Next.js
- Webhook system (FastAPI → Next.js)
- API authentication
- CORS configured

---

## 📁 Directory Structure

```
0711-OS/
├── api/                     # Control Plane API (Port 4080)
│   ├── routes/              # Auth, subscriptions, deployments, onboarding
│   ├── models/              # SQLAlchemy models
│   └── schemas/             # Pydantic validation
├── console/
│   ├── backend/             # Console Backend (Port 4010)
│   │   ├── routes/          # Chat, data, MCPs, ingest
│   │   └── websocket/       # Real-time chat
│   └── frontend/            # Console Frontend (Port 4020)
│       └── src/             # React components
├── apps/
│   └── website/             # Marketing Website (Port 4000)
│       └── app/
│           ├── onboarding/  # Onboarding wizard
│           └── admin/       # Admin mockup
├── core/                    # Platform core (lakehouse, MCPs)
├── ingestion/               # Data pipeline
├── lakehouse/               # Delta Lake + Lance
├── mcps/                    # MCP SDK + implementations
├── orchestrator/            # Model management
└── inference/               # vLLM server

```

---

## 🔧 Configuration Files

| File | Purpose |
|------|---------|
| `.env` (root) | Control Plane API config |
| `console/backend/.env` | Console Backend config |
| `apps/website/.env.local` | Marketing website config |
| `console/frontend/.env.local` | Console UI config |
| `docker-compose.yml` | All Docker services (40XX ports) |

---

## 🎨 Design System

**Console Frontend** uses Anthropic-inspired design:
- Clean, minimal interface
- Light backgrounds (white/cream)
- Monospace fonts for technical content
- Subtle borders and spacing
- Professional, accessible

**Marketing/Onboarding** uses 0711 brand:
- Dark theme (#141413)
- Orange accent (#d97757)
- Poppins (headings) + Lora (body)
- Premium, sophisticated feel

---

## 🛠️ Development

### View Logs
```bash
tail -f /tmp/0711_api.log                  # Control Plane
tail -f /tmp/0711_console_backend.log      # Console Backend
tail -f /tmp/0711_website.log              # Website
tail -f /tmp/0711_console_frontend.log     # Console UI
```

### Check Services
```bash
curl http://localhost:4080/health          # Control Plane
curl http://localhost:4010/health          # Console Backend
curl http://localhost:4000                 # Website
curl http://localhost:4020                 # Console UI
```

### Database Access
```bash
docker exec -it 0711-postgres psql -U 0711 -d 0711_control
```

---

## 📦 What's Complete

✅ **Control Plane** (Billing/Customer Management)
✅ **Marketing Website** (Onboarding Flow)
✅ **Console Backend** (Chat/Data API)
✅ **Console Frontend** (UI for data interaction)
✅ **PostgreSQL** (Dedicated database)
✅ **All on 40XX ports** (No conflicts!)

---

## 🚧 Optional Services

These can be started via docker-compose when needed:

```bash
# Start MinIO (S3 storage)
docker compose up -d minio

# Start vLLM (requires GPU)
docker compose --profile gpu up -d vllm

# Start Embeddings
docker compose up -d embeddings

# Start all infrastructure
docker compose up -d
```

---

## 🎉 Summary

**The 0711 Platform is FULLY OPERATIONAL!**

You have:
- Complete onboarding flow
- Working control plane for customer management
- Functional console for chatting with data
- All services isolated on 40XX ports
- No interference with existing projects (buhl, ETIM, etc.)

**Next Steps:**
1. Add SSH tunnel ports (4000, 4010, 4020, 4080)
2. Access from your Mac browser
3. Test onboarding flow
4. Test console chat interface
5. Start adding real data!

---

**Built with 0711 Intelligence** 🚀
