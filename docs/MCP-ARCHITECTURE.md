# MCP Architecture - Model Context Protocol

> Domain-specific AI experts that extend the base LLM with specialized knowledge.

## Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           0711-OS MCP SYSTEM                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         MCP ROUTER                                   │   │
│  │                                                                      │   │
│  │  Customer Query → Classify → Route to MCP → Execute → Return        │   │
│  └──────────────────────────────┬──────────────────────────────────────┘   │
│                                 │                                           │
│         ┌───────────────────────┼───────────────────────┐                  │
│         │                       │                       │                  │
│         ▼                       ▼                       ▼                  │
│  ┌─────────────┐        ┌─────────────┐        ┌─────────────┐            │
│  │    CTAX     │        │     LAW     │        │   TENDER    │            │
│  │             │        │             │        │             │            │
│  │ German Tax  │        │   Legal &   │        │ Procurement │            │
│  │ VAT/ELSTER  │        │  Contracts  │        │   Bidding   │            │
│  │             │        │             │        │             │            │
│  │ LoRA: ctax  │        │ LoRA: law   │        │LoRA: tender │            │
│  └─────────────┘        └─────────────┘        └─────────────┘            │
│                                                                             │
│  ┌─────────────┐        ┌─────────────┐        ┌─────────────┐            │
│  │   MARKET    │        │   PUBLISH   │        │  SYNDICATE  │            │
│  │             │        │             │        │             │            │
│  │  Competitor │        │   Content   │        │   Partner   │            │
│  │  Analysis   │        │ Publishing  │        │   Network   │            │
│  └─────────────┘        └─────────────┘        └─────────────┘            │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    SHARED INFRASTRUCTURE                             │   │
│  │                                                                      │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │   │
│  │  │  Qwen    │  │ Lakehouse│  │  Vector  │  │   LoRA   │            │   │
│  │  │  72B     │  │  Delta   │  │  Lance   │  │ Adapters │            │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Core MCPs (Ship with Platform)

| MCP | Purpose | LoRA | Key Features |
|-----|---------|------|--------------|
| **CTAX** | German Tax | ctax-lora | VAT, ELSTER, Compliance |
| **LAW** | Legal/Contracts | law-lora | BGB, GDPR, Contracts |
| **TENDER** | Procurement | tender-lora | Bid analysis, Pricing |
| **MARKET** | Competitive Intel | - | Web search, Analysis |
| **PUBLISH** | Content Publishing | - | SEO, Datasheets |
| **SYNDICATE** | Partner Network | - | Distribution feeds |

## MCP Structure

```python
class BaseMCP:
    """Base class for all MCPs"""
    
    name: str              # Unique identifier (e.g., "ctax")
    version: str           # Semantic version
    lora_adapter: str      # Path to LoRA weights
    
    async def process(self, input, context) -> MCPResponse:
        """Main processing method - implement business logic"""
        pass
    
    # Built-in capabilities:
    async def generate(prompt, ...)     # LLM inference
    async def embed(text)               # Generate embeddings
    def query_data(sql)                 # Query lakehouse
    def search_similar(vector)          # Vector search
```

## Creating a New MCP

```python
# mcps/core/my_domain.py

from mcps.sdk import BaseMCP, MCPResponse

class MyDomainMCP(BaseMCP):
    name = "mydomain"
    version = "1.0.0"
    lora_adapter = "adapters/mydomain-lora"  # Optional
    
    SYSTEM_PROMPT = """You are a specialist in [domain]..."""
    
    async def process(self, input, context=None) -> MCPResponse:
        # 1. Search relevant documents
        docs = self.query_data("SELECT * FROM documents WHERE ...")
        
        # 2. Build prompt with context
        prompt = f"{self.SYSTEM_PROMPT}\n\nContext: {docs}\n\nQuery: {input}"
        
        # 3. Generate response (uses base LLM + optional LoRA)
        response = await self.generate(prompt=prompt, max_tokens=1000)
        
        # 4. Return structured response
        return MCPResponse(
            data={"answer": response},
            confidence=0.85,
            model_used=f"qwen+{self.name}-lora"
        )
```

## MCP Router

Routes queries to the appropriate MCP based on classification:

```python
# orchestrator/mcp/mcp_router.py

class MCPRouter:
    def __init__(self):
        self.mcps = {
            "ctax": MCPConfig(url="http://localhost:7770", ...),
            "law": MCPConfig(url="http://localhost:7771", ...),
            "tender": MCPConfig(url="http://localhost:7772", ...),
        }
    
    async def route(self, query: str, customer_id: str) -> MCPResponse:
        # 1. Classify query intent
        mcp_name = await self.classify(query)  # "ctax", "law", etc.
        
        # 2. Get customer context (lakehouse, LoRA)
        context = self.get_customer_context(customer_id)
        
        # 3. Route to MCP
        return await self.mcps[mcp_name].process(query, context)
```

## LoRA Integration

Each MCP can have a domain-specific LoRA adapter:

```
/data/loras/
├── ctax/
│   ├── adapter_config.json
│   └── adapter_model.safetensors
├── law/
│   ├── adapter_config.json
│   └── adapter_model.safetensors
└── tender/
    └── ...
```

### Hot-Swapping LoRAs

```python
# vLLM supports runtime LoRA loading
POST /v1/chat/completions
{
    "model": "Qwen/Qwen2.5-72B-Instruct",
    "lora_path": "/data/loras/ctax",  # Load CTAX adapter
    "messages": [...]
}
```

## Shared vs Per-Customer

```
┌───────────────────────────────────────────────────────────────┐
│                    DEPLOYMENT MODEL                            │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  SHARED (deployed once, used by all):                         │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐                         │
│  │  CTAX   │ │   LAW   │ │ TENDER  │                         │
│  └─────────┘ └─────────┘ └─────────┘                         │
│                                                               │
│  PER-CUSTOMER (isolated):                                     │
│  ┌───────────────────────────────────────┐                   │
│  │  Customer A                            │                   │
│  │  ├── Lakehouse (Delta + Lance)        │                   │
│  │  ├── LoRA Adapter (fine-tuned)        │                   │
│  │  └── MinIO Bucket                     │                   │
│  └───────────────────────────────────────┘                   │
│  ┌───────────────────────────────────────┐                   │
│  │  Customer B                            │                   │
│  │  ├── Lakehouse (Delta + Lance)        │                   │
│  │  ├── LoRA Adapter (fine-tuned)        │                   │
│  │  └── MinIO Bucket                     │                   │
│  └───────────────────────────────────────┘                   │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

## API Usage

### Query via Router

```bash
POST /api/mcp/query
{
    "query": "Wie berechne ich die Vorsteuer für eine Rechnung mit 19% MwSt?",
    "customer_id": "acme-corp"
}

# Router classifies as "ctax" → routes to CTAX MCP
```

### Direct MCP Call

```bash
POST /api/mcp/ctax/process
{
    "input": {
        "task_type": "calculate_vat",
        "net_amount": 1000,
        "vat_rate": 0.19
    },
    "customer_id": "acme-corp"
}

# Response:
{
    "data": {
        "net_amount": 1000.00,
        "vat_amount": 190.00,
        "gross_amount": 1190.00
    },
    "confidence": 0.99,
    "model_used": "calculation"
}
```

## MCP Registry

```python
from mcps.registry import get_registry

registry = get_registry()

# List available MCPs
registry.list_core()      # ["ctax", "law", "tender", ...]
registry.list_installed() # All registered MCPs

# Get MCP instance
ctax = registry.get("ctax")
response = await ctax.process("Vorsteuerabzug Frage...")

# Check if core
registry.is_core("ctax")  # True
```

## Marketplace MCPs (Future)

Third-party MCPs can be installed from the marketplace:

```bash
# Install from marketplace
POST /api/marketplace/install
{
    "mcp_id": "invoice-pro",
    "license_key": "xxx"
}

# MCP is downloaded and registered
registry.get("invoice-pro")  # Now available
```

## Key Benefits

1. **Modularity**: Each domain is encapsulated in its own MCP
2. **Specialization**: Domain-specific LoRA adapters improve quality
3. **Reusability**: MCPs are shared across customers (60% fewer containers)
4. **Extensibility**: New domains = new MCPs, no core changes
5. **Isolation**: Customer data stays isolated via context injection

## Next Steps

1. **Train LoRA adapters** for each domain (CTAX, LAW, TENDER)
2. **Build MCP Marketplace** for third-party extensions
3. **Add more MCPs**: HR, Accounting, Inventory, etc.
4. **Multi-lingual MCPs**: English, French, etc.
