# Orchestrator MCP - Documentation

**Version:** 1.0.0
**Author:** 0711 Intelligence
**Last Updated:** 2025-01-27

## Overview

The Orchestrator MCP is the central brain of the 0711 platform. It orchestrates all platform services and provides a unified interface for:

- Initial customer deployment via Cradle
- Incremental updates via MCP Central
- Database access with authorization
- MCP Marketplace management
- Intelligence layer (change detection)
- Continuous learning (V2)

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR MCP                            │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────────┐    ┌──────────────────┐                │
│  │  User Registry   │    │  Installation DB │                │
│  │  (MCP Central)   │    │  (Cradle)        │                │
│  └──────────────────┘    └──────────────────┘                │
│                                                                │
│  ┌──────────────────┐    ┌──────────────────┐                │
│  │  Database        │    │  Marketplace     │                │
│  │  Gateway         │    │  Gateway         │                │
│  └──────────────────┘    └──────────────────┘                │
│                                                                │
│  ┌──────────────────┐    ┌──────────────────┐                │
│  │  Change          │    │  Cradle Client   │                │
│  │  Detector        │    │                  │                │
│  └──────────────────┘    └──────────────────┘                │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

## API Reference

### Initial Deployment

#### `initialize_customer()`

Initialize new customer deployment.

**Arguments:**
- `company_name` (str): Company name
- `contact_email` (str): Primary contact email
- `data_sources` (List[str]): List of data source paths
- `deployment_target` (str): 'on-premise', 'cloud', or 'hybrid'
- `mcps` (Optional[List[str]]): List of MCPs to enable
- `installation_params` (Optional[Dict]): Processing configuration

**Returns:**
```python
{
    "success": True,
    "customer_id": "eaton",
    "user_id": "550e8400-...",
    "user_token": "eyJhbGc...",
    "deployment": {...},
    "stats": {...},
    "image_archive": "/path/to/archive.tar",
    "enabled_mcps": ["ctax", "law", "etim"]
}
```

**Example:**
```python
from mcps.registry import get_mcp

orchestrator = get_mcp("orchestrator")

result = await orchestrator.initialize_customer(
    company_name="EATON",
    contact_email="max@eaton.com",
    data_sources=["/data/eaton-import"],
    deployment_target="on-premise",
    mcps=["ctax", "law", "etim"],
    installation_params={
        "embedding_model": "intfloat/multilingual-e5-large",
        "vision_enabled": True,
        "graph_extraction_enabled": True
    }
)

print(f"Customer {result['customer_id']} initialized")
print(f"User token: {result['user_token']}")
```

### Incremental Updates

#### `process_new_documents()`

Process new documents using MCP Central services.

**Arguments:**
- `customer_id` (str): Customer identifier
- `user_token` (str): User authentication token
- `file_paths` (List[str]): List of file paths

**Returns:**
```python
{
    "success": True,
    "customer_id": "eaton",
    "processed_files": 10,
    "results": [...]
}
```

**Example:**
```python
result = await orchestrator.process_new_documents(
    customer_id="eaton",
    user_token="eyJhbGc...",
    file_paths=[
        "/data/new-document-1.pdf",
        "/data/new-document-2.docx"
    ]
)
```

#### `generate_embeddings()`

Generate embeddings via MCP Central.

**Arguments:**
- `customer_id` (str): Customer identifier
- `user_token` (str): User authentication token
- `texts` (List[str]): List of texts to embed

**Returns:**
```python
{
    "success": True,
    "embeddings": [[0.1, 0.2, ...], ...],
    "total": 10,
    "model": "multilingual-e5-large"
}
```

### Database Access

#### `query_customer_database()`

Query customer database with authorization.

**Arguments:**
- `customer_id` (str): Customer identifier
- `user_token` (str): User authentication token
- `database` (str): Database type ('neo4j', 'lakehouse', 'minio')
- `query` (str): Query string
- `require_approval` (bool): Require human approval for writes

**Returns:**
```python
{
    "success": True,
    "results": [...]
}
```

**Example:**
```python
result = await orchestrator.query_customer_database(
    customer_id="eaton",
    user_token="eyJhbGc...",
    database="lakehouse",
    query="SELECT * FROM documents WHERE category = 'tax' LIMIT 10",
    require_approval=False  # Read-only, no approval needed
)
```

### MCP Marketplace

#### `list_marketplace_mcps()`

List available MCPs in marketplace.

**Arguments:**
- `user_token` (str): User authentication token
- `category` (Optional[str]): Filter by category
- `search` (Optional[str]): Search string

**Returns:**
```python
{
    "success": True,
    "total": 7,
    "mcps": [...],
    "customer_tier": "professional"
}
```

#### `install_mcp()`

Install MCP for customer.

**Arguments:**
- `user_token` (str): User authentication token
- `mcp_name` (str): MCP name
- `license_key` (Optional[str]): License key (generated if not provided)

**Returns:**
```python
{
    "success": True,
    "installation_id": "inst-123",
    "mcp_name": "etim",
    "license_key": "0711-ABCD1234",
    "expires_at": "2026-01-27"
}
```

#### `connect_mcp()`

Connect MCP as input or output.

**Arguments:**
- `user_token` (str): User authentication token
- `mcp_name` (str): MCP name
- `direction` (str): 'input' or 'output'
- `config` (Optional[Dict]): Connection configuration

**Returns:**
```python
{
    "success": True,
    "mcp_name": "etim",
    "direction": "output",
    "connected": True,
    "test_result": {...}
}
```

#### `query_mcp()`

Query MCP service.

**Arguments:**
- `user_token` (str): User authentication token
- `mcp_name` (str): MCP name
- `query` (str): Query string
- `context` (Optional[Dict]): Query context

**Returns:**
```python
{
    "success": True,
    "result": {...}
}
```

### Intelligence Layer

#### `get_data_changes()`

Detect data changes and get service offers.

**Arguments:**
- `customer_id` (str): Customer identifier
- `user_token` (str): User authentication token

**Returns:**
```python
{
    "success": True,
    "customer_id": "eaton",
    "changes": {
        "new_documents": 500,
        "new_images": 100,
        "graph_growth_percent": 15.0
    },
    "service_offers": [...],
    "has_significant_changes": True
}
```

### Resource Methods (Read-Only)

#### `get_customer_stats()`

Get customer statistics from Docker instance.

#### `get_installation_config()`

Load installation configuration from Cradle DB.

#### `get_installed_mcps()`

List installed MCPs for customer.

#### `list_customer_deployments()`

List all active customer deployments.

## REST API

The Orchestrator MCP is exposed via REST API at `/api/orchestrator`.

### Endpoints

#### POST `/api/orchestrator/initialize-customer`

Initialize new customer.

**Request:**
```json
{
  "company_name": "EATON",
  "contact_email": "max@eaton.com",
  "data_sources": ["/data/eaton-import"],
  "deployment_target": "on-premise",
  "mcps": ["ctax", "law", "etim"]
}
```

#### POST `/api/orchestrator/process-documents`

Process new documents.

**Request:**
```json
{
  "customer_id": "eaton",
  "file_paths": ["/data/new-doc.pdf"]
}
```

#### POST `/api/orchestrator/query-database`

Query customer database.

**Request:**
```json
{
  "customer_id": "eaton",
  "database": "lakehouse",
  "query": "SELECT * FROM documents LIMIT 10",
  "require_approval": false
}
```

#### GET `/api/orchestrator/marketplace/mcps`

List marketplace MCPs.

**Query Parameters:**
- `category` (optional): Filter by category
- `search` (optional): Search string

#### POST `/api/orchestrator/marketplace/install`

Install MCP.

**Request:**
```json
{
  "mcp_name": "etim",
  "license_key": null
}
```

#### POST `/api/orchestrator/marketplace/connect`

Connect MCP.

**Request:**
```json
{
  "mcp_name": "etim",
  "direction": "output",
  "config": {}
}
```

#### POST `/api/orchestrator/marketplace/query`

Query MCP.

**Request:**
```json
{
  "mcp_name": "etim",
  "query": "Classify products in catalog",
  "context": {}
}
```

#### GET `/api/orchestrator/changes/{customer_id}`

Get data changes.

#### GET `/api/orchestrator/stats/{customer_id}`

Get customer statistics.

#### GET `/api/orchestrator/config/{customer_id}`

Get installation configuration.

#### GET `/api/orchestrator/deployments`

List all deployments.

## Installation Parameters

Installation parameters are the "golden source" for consistent processing. They are saved during initial deployment and used for all future updates.

**Stored in:** Cradle Installation DB

**Structure:**
```json
{
  "customer_id": "eaton",
  "company_name": "EATON",
  "deployment_date": "2025-01-27T12:00:00Z",
  "user_id": "550e8400-...",
  "contact_email": "max@eaton.com",
  "deployment_target": "on-premise",

  "embedding_config": {
    "model": "intfloat/multilingual-e5-large",
    "batch_size": 128,
    "normalize": true
  },

  "vision_config": {
    "model": "microsoft/Florence-2-large",
    "languages": ["de", "en"],
    "ocr_enabled": true
  },

  "chunking_config": {
    "strategy": "structure-aware",
    "chunk_size": 512,
    "overlap": 50
  },

  "graph_config": {
    "enabled": true,
    "entity_types": ["company", "person", "product"],
    "relationship_threshold": 0.7
  },

  "initial_stats": {
    "total_files": 617,
    "total_documents": 31807,
    "graph_nodes": 15420
  },

  "enabled_mcps": ["ctax", "law", "etim"]
}
```

## Security & Authorization

### User Authentication

All operations require a valid JWT token obtained from MCP Central.

**Token format:**
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Token payload:**
```json
{
  "user_id": "550e8400-...",
  "customer_id": "eaton",
  "email": "max@eaton.com",
  "role": "customer_admin",
  "exp": 1706342400
}
```

### Database Access

Write operations require human approval (Human-in-the-Loop).

**Approval flow:**
1. Write operation detected
2. Approval request created
3. User notified (email/console)
4. User approves/rejects
5. Operation executes (or fails)

**Timeout:** 5 minutes

### Permissions

Role-based permissions:

- `platform_admin`: All permissions
- `customer_admin`: Customer-level admin
- `customer_user`: Limited access

## Error Handling

All methods return structured errors:

```python
try:
    result = await orchestrator.initialize_customer(...)
except ValueError as e:
    # Invalid parameters
    print(f"Error: {e}")
except PermissionError as e:
    # Authorization failed
    print(f"Permission denied: {e}")
except Exception as e:
    # Unexpected error
    print(f"Unexpected error: {e}")
```

## Logging

All operations are logged:

```
2025-01-27 12:00:00 INFO Orchestrator MCP initialized
2025-01-27 12:01:00 INFO Initializing customer: EATON
2025-01-27 12:01:05 INFO ✓ User created: 550e8400-...
2025-01-27 12:05:00 INFO ✓ Processing complete: 31807 documents
2025-01-27 12:10:00 INFO ✓ Build complete for eaton
```

## Best Practices

1. **Always save initial images** - Never delete versioned images
2. **Use installation parameters** - Ensure consistent processing
3. **Test approvals** - Verify Human-in-the-Loop workflow
4. **Monitor changes** - Use change detector proactively
5. **Audit everything** - Enable audit logging

## Support

- Documentation: https://docs.0711.io
- Email: support@0711.io
- GitHub: https://github.com/0711/0711-OS

---

**Built with ❤️ by 0711 Intelligence**
