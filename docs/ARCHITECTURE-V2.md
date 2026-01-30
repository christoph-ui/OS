# 0711-OS Architecture V2: Decoupled Data Pipeline

## Problem with Current Approach

```
Current: Data → Ingestion → Baked into Deploy
         ↓
         Complex, slow, data tied to image
```

## New Architecture: Playground → Export → Import

```
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 1: PLAYGROUND (0711 Cloud / H200 Cluster)                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Customer Portal                                                │
│       │                                                         │
│       ▼                                                         │
│  ┌─────────────────┐                                           │
│  │  Upload Service │  Raw files → MinIO staging bucket         │
│  └────────┬────────┘                                           │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              ADAPTIVE INGESTION PIPELINE                 │   │
│  │                                                          │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │   │
│  │  │ Crawler  │→ │Classifier│→ │Processor │→ │ Loader  │ │   │
│  │  │          │  │ (Claude) │  │(Embed)   │  │         │ │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │   │
│  └─────────────────────────────────────────────────────────┘   │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              STAGING LAKEHOUSE (per-tenant)              │   │
│  │                                                          │   │
│  │  MinIO: staging-{customer_id}/                          │   │
│  │  ├── raw/           # Original files                    │   │
│  │  ├── delta/         # Delta Lake tables                 │   │
│  │  ├── vectors/       # LanceDB indices                   │   │
│  │  ├── metadata/      # Document metadata, relationships  │   │
│  │  └── handlers/      # Claude-generated parsers          │   │
│  │                                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              PLAYGROUND CONSOLE                          │   │
│  │                                                          │   │
│  │  • Test queries against their data                      │   │
│  │  • Validate ingestion quality                           │   │
│  │  • Preview MCP responses                                │   │
│  │  • Adjust LoRA training data                            │   │
│  │                                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Customer clicks "Deploy"
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 2: DEPLOYMENT DECISION                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐              ┌─────────────────┐          │
│  │   0711 Cloud    │              │    On-Premise   │          │
│  │   (Managed)     │              │    (Cradle)     │          │
│  │                 │              │                 │          │
│  │  Keep on H200   │              │  Download ISO   │          │
│  │  cluster        │              │  Install local  │          │
│  └─────────────────┘              └─────────────────┘          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 3: CLEAN DEPLOY + DATA SYNC                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Step 1: Deploy Clean Image                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  0711-OS Base Image (NO CUSTOMER DATA)                   │   │
│  │                                                          │   │
│  │  • vLLM (Mixtral 8x7B) - model weights only             │   │
│  │  • Embeddings service                                    │   │
│  │  • Empty lakehouse schema                               │   │
│  │  • Console UI                                           │   │
│  │  • MCP stubs (connect to shared or deploy local)        │   │
│  │  • Data Import Service (NEW)                            │   │
│  │                                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Step 2: System boots, announces ready                         │
│                                                                 │
│  Step 3: Data Sync (automatic)                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                                                          │   │
│  │  Staging Lake ──────────▶ Production Lake               │   │
│  │                                                          │   │
│  │  Export Bundle:          Import Process:                │   │
│  │  • delta/*.parquet      → Delta Lake tables             │   │
│  │  • vectors/*.lance      → LanceDB indices               │   │
│  │  • metadata/*.json      → PostgreSQL                    │   │
│  │  • lora/*.safetensors   → vLLM LoRA adapter            │   │
│  │  • handlers/*.py        → Custom ingestion handlers     │   │
│  │                                                          │   │
│  │  Transfer: HTTPS/S3 sync (resume on failure)            │   │
│  │                                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Step 4: Ready for use                                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## New Components Needed

### 1. Data Export Service (`orchestrator/export/`)

```python
class DataExporter:
    """Export staging lakehouse to portable bundle"""
    
    async def export_customer(self, customer_id: str) -> ExportBundle:
        """
        Creates portable data bundle:
        - Delta tables (parquet files)
        - Vector indices (lance format)
        - Metadata (JSON)
        - LoRA weights (safetensors)
        - Custom handlers (Python files)
        """
        pass
    
    async def create_manifest(self, bundle: ExportBundle) -> Manifest:
        """
        Creates manifest.json with:
        - Version info
        - Checksums
        - Schema versions
        - Import instructions
        """
        pass
```

### 2. Data Import Service (`orchestrator/import/`)

```python
class DataImporter:
    """Import data bundle into fresh 0711-OS instance"""
    
    async def import_from_url(self, manifest_url: str) -> ImportResult:
        """
        Called by fresh instance after boot:
        1. Download manifest
        2. Verify checksums
        3. Stream delta tables
        4. Stream vector indices
        5. Load LoRA weights
        6. Signal ready
        """
        pass
    
    async def resume_import(self, import_id: str) -> ImportResult:
        """Resume interrupted import (network issues, etc.)"""
        pass
```

### 3. Sync Protocol

```
Staging (0711 Cloud)          Target (Cloud/On-Prem)
        │                              │
        │   1. /api/deploy/initiate    │
        │   customer_id, target_url    │
        │────────────────────────────▶│
        │                              │
        │   2. Target boots clean      │
        │      image, calls back       │
        │◀────────────────────────────│
        │   POST /api/sync/ready       │
        │   { instance_id, api_key }   │
        │                              │
        │   3. Stream data bundle      │
        │────────────────────────────▶│
        │   GET /export/{customer_id}  │
        │   Range: bytes=0-            │
        │                              │
        │   4. Import complete         │
        │◀────────────────────────────│
        │   POST /api/sync/complete    │
        │                              │
        │   5. Ongoing sync (optional) │
        │◀──────────────────────────▶│
        │   Delta changes, new docs    │
```

## Benefits

1. **Clean Images**: Docker images are versioned, reproducible, data-free
2. **Fast Iteration**: Update OS without touching customer data
3. **Easy Migration**: Move between cloud/on-prem without re-ingestion
4. **Resumable**: Network issues don't mean starting over
5. **Testable**: Customer validates in playground before committing
6. **Scalable**: Ingestion happens on powerful H200 cluster
7. **Compliant**: Customer can delete staging after migration

## Implementation Priority

### Phase 1: Playground + Export (Week 1-2)
- [ ] Staging lakehouse schema
- [ ] Playground console UI
- [ ] Export service
- [ ] Manifest format

### Phase 2: Clean Image + Import (Week 2-3)
- [ ] Base image build (no data)
- [ ] Import service
- [ ] Boot-time sync trigger
- [ ] Progress WebSocket

### Phase 3: Sync Protocol (Week 3-4)
- [ ] Secure handshake
- [ ] Resumable streaming
- [ ] Delta sync (ongoing changes)
- [ ] On-prem installer (Cradle)
