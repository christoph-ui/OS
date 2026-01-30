# MCP Marketplace Integration

**Version:** 1.0.0
**Last Updated:** 2025-01-27

---

## Overview

The 0711 MCP Marketplace provides one-click installation of AI-powered MCPs (Model Context Protocols). MCPs are specialized AI tools that solve specific business problems.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     MCP MARKETPLACE                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  CORE MCPs (1st Party, Always Available):                      │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐       │
│  │ CTAX │ │ LAW  │ │TENDER│ │ ETIM │ │MARKET│ │PUBLISH│       │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘       │
│                                                                 │
│  3RD PARTY MCPs (Marketplace, Optional):                       │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                          │
│  │DATEV │ │ SAP  │ │Invoice│ │ ...  │                          │
│  └──────┘ └──────┘ └──────┘ └──────┘                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ via Orchestrator MCP
                              │
              ┌───────────────┴────────────────┐
              │                                │
              ▼                                ▼
    ┌─────────────────┐            ┌─────────────────┐
    │  Customer A     │            │  Customer B     │
    │                 │            │                 │
    │  enabled_mcps:  │            │  enabled_mcps:  │
    │  • CTAX ✓       │            │  • LAW ✓        │
    │  • ETIM ✓       │            │  • TENDER ✓     │
    │  • DATEV ✓      │            │                 │
    │                 │            │                 │
    │  connected:     │            │  connected:     │
    │  In:  [SAP]     │            │  In:  [DATEV]   │
    │  Out: [ETIM]    │            │  Out: [PUBLISH] │
    └─────────────────┘            └─────────────────┘
```

## MCP Types

### 1. Shared MCPs

**Deployment:** One instance serves all customers
**Examples:** ETIM, MARKET, PUBLISH

**Characteristics:**
- Deployed centrally (not per-customer)
- Accessed via MCP Router
- Customer data isolated at query level
- Efficient (60% fewer containers)

**Connection:**
```python
# Customer queries shared MCP
result = await orchestrator.query_mcp(
    user_token=token,
    mcp_name="etim",
    query="Classify products",
    context={"customer_id": "eaton"}  # Data isolation
)
```

### 2. Sidecar MCPs

**Deployment:** Dedicated container per customer
**Examples:** Custom MCPs, high-security MCPs

**Characteristics:**
- Deployed in customer's Docker network
- Full data isolation
- Can access customer databases directly
- Higher resource usage

**Deployment:**
```bash
# Automatically deployed when installed
POST /api/orchestrator/marketplace/install
{
  "mcp_name": "custom-mcp",
  "license_key": "0711-..."
}

# Creates container: {customer_id}-custom-mcp
```

### 3. External API MCPs

**Deployment:** External service (3rd party)
**Examples:** DATEV Connector, SAP Bridge

**Characteristics:**
- Not deployed by 0711
- Accessed via API
- OAuth/API key authentication
- May have external costs

**Connection:**
```python
result = await orchestrator.connect_mcp(
    user_token=token,
    mcp_name="datev",
    direction="input",
    config={
        "api_url": "https://api.datev.de",
        "api_key": "...",
        "client_id": "..."
    }
)
```

## Database Schema

### mcps Table

```sql
CREATE TABLE mcps (
    id UUID PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    version VARCHAR(20),
    category VARCHAR(50),  -- 'finance', 'legal', 'logistics', etc.
    description TEXT,

    -- Ownership
    developer_id UUID REFERENCES mcp_developers(id),  -- NULL = 0711 Core

    -- Approval Workflow
    status VARCHAR(20) DEFAULT 'pending',  -- pending, approved, rejected
    approved_by_id UUID REFERENCES users(id),
    approved_at TIMESTAMP,
    rejection_reason TEXT,

    -- Connection
    connection_type VARCHAR(50),  -- 'shared', 'sidecar', 'api'
    api_docs_url VARCHAR(500),
    setup_instructions TEXT,

    -- Docker (for sidecar MCPs)
    docker_image VARCHAR(255),
    docker_config JSONB,

    -- External API (for api MCPs)
    oauth_config JSONB,
    connection_test_endpoint VARCHAR(500),

    -- Pricing
    pricing_model VARCHAR(20),  -- 'free', 'subscription', 'usage'
    monthly_price_cents INTEGER,
    usage_price_per_unit_cents INTEGER,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### mcp_installations Table

```sql
CREATE TABLE mcp_installations (
    id UUID PRIMARY KEY,
    customer_id UUID REFERENCES customers(id),
    mcp_id UUID REFERENCES mcps(id),

    -- Installation
    installed_at TIMESTAMP DEFAULT NOW(),
    installed_by UUID REFERENCES users(id),

    -- License
    license_key VARCHAR(255),
    license_expires_at TIMESTAMP,

    -- Status
    status VARCHAR(20) DEFAULT 'active',  -- active, suspended, canceled

    -- Usage tracking (for billing)
    total_queries INTEGER DEFAULT 0,
    last_used_at TIMESTAMP,

    UNIQUE(customer_id, mcp_id)
);
```

### Customer MCP Fields

```sql
-- customers table additions
enabled_mcps JSONB DEFAULT '{}'::jsonb
-- Example: {"etim": true, "ctax": true, "law": false}

connected_mcps JSONB DEFAULT '{"input": [], "output": []}'::jsonb
-- Example: {"input": ["sap", "datev"], "output": ["etim", "publish"]}
```

## API Reference

### List MCPs

**Endpoint:** `GET /api/orchestrator/marketplace/mcps`

**Query Parameters:**
- `category` (optional): Filter by category
- `search` (optional): Search in name/description

**Response:**
```json
{
  "success": true,
  "total": 7,
  "mcps": [
    {
      "id": "uuid",
      "name": "ctax",
      "version": "2.0.0",
      "category": "finance",
      "description": "German tax engine",
      "connection_type": "shared",
      "pricing_model": "subscription",
      "monthly_price_eur": 500.0,
      "developer_name": "0711 Intelligence",
      "installation_count": 1250,
      "avg_rating": 4.9,
      "installed": true,
      "connected_as_input": false,
      "connected_as_output": true
    }
  ],
  "customer_tier": "professional"
}
```

### Install MCP

**Endpoint:** `POST /api/orchestrator/marketplace/install`

**Body:**
```json
{
  "mcp_name": "etim",
  "license_key": null
}
```

**Response:**
```json
{
  "success": true,
  "installation_id": "inst-123",
  "mcp_name": "etim",
  "license_key": "0711-ABCD1234EFGH5678",
  "expires_at": "2026-01-27T12:00:00Z",
  "connection_type": "shared",
  "deployment": null
}
```

### Connect MCP

**Endpoint:** `POST /api/orchestrator/marketplace/connect`

**Body:**
```json
{
  "mcp_name": "etim",
  "direction": "output",
  "config": {}
}
```

**Response:**
```json
{
  "success": true,
  "mcp_name": "etim",
  "direction": "output",
  "connected": true,
  "test_result": {
    "status": "ok",
    "latency_ms": 45
  }
}
```

### Query MCP

**Endpoint:** `POST /api/orchestrator/marketplace/query`

**Body:**
```json
{
  "mcp_name": "etim",
  "query": "Classify products in catalog",
  "context": {}
}
```

**Response:**
```json
{
  "success": true,
  "result": {
    "classifications": [...]
  }
}
```

## Input vs Output MCPs

### Input MCPs (Data Sources)

Pull data FROM external systems INTO your platform.

**Examples:**
- SAP Connector (ERP data)
- DATEV Connector (Accounting data)
- PIM Connector (Product data)
- DAM Connector (Asset data)

**Usage:**
```python
# Connect SAP as input
await orchestrator.connect_mcp(
    user_token=token,
    mcp_name="sap",
    direction="input",
    config={
        "host": "sap.company.com",
        "username": "...",
        "password": "..."
    }
)

# Data flows: SAP → 0711 Lakehouse
```

### Output MCPs (Target Systems)

Push data FROM your platform TO external systems.

**Examples:**
- ETIM Export (Product classification)
- Syndicate (Distribution to partners)
- Publish (E-commerce platforms)

**Usage:**
```python
# Connect ETIM as output
await orchestrator.connect_mcp(
    user_token=token,
    mcp_name="etim",
    direction="output"
)

# Data flows: 0711 Lakehouse → ETIM Classification → Export
```

## Connection Testing

All connections are tested before activation:

```python
test_result = await orchestrator.connect_mcp(
    user_token=token,
    mcp_name="sap",
    direction="input",
    config={...}
)

# test_result:
{
    "status": "ok",  # or "error"
    "latency_ms": 150,
    "message": "Connected successfully",
    "data_sample": {...}  # Sample data if input MCP
}
```

If test fails, connection is not saved.

## License Management

### License Key Format

```
0711-{SHA256_HASH[:32]}

Example: 0711-ABCD1234EFGH5678IJKL9012MNOP3456
```

### License Types

1. **Free:** No license key needed
2. **Subscription:** Annual license key
3. **Usage-based:** Pay per query/operation

### License Validation

```python
from orchestrator.marketplace.license_manager import LicenseManager

# Generate
key = LicenseManager.generate_license_key("eaton", "etim")

# Validate
valid = LicenseManager.validate_license_key(key, mcp_id)

# Check expiration
expired = LicenseManager.is_license_expired(key, expires_at)
```

## Billing & Usage Tracking

All MCP queries are tracked for billing:

```sql
-- Usage tracking (in future implementation)
CREATE TABLE mcp_usage (
    id UUID PRIMARY KEY,
    customer_id UUID,
    mcp_id UUID,
    query_tokens INTEGER,
    processing_time_ms INTEGER,
    billable_units INTEGER DEFAULT 1,
    cost_cents INTEGER,
    occurred_at TIMESTAMP DEFAULT NOW()
);
```

## Frontend Integration

### React Component Example

```typescript
import { useState, useEffect } from 'react';

export function MCPMarketplace() {
  const [mcps, setMCPs] = useState([]);
  const [installedMCPs, setInstalledMCPs] = useState([]);

  useEffect(() => {
    // Fetch available MCPs
    fetch('/api/orchestrator/marketplace/mcps')
      .then(r => r.json())
      .then(data => setMCPs(data.mcps));
  }, []);

  const handleInstall = async (mcpName: string) => {
    const response = await fetch('/api/orchestrator/marketplace/install', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mcp_name: mcpName })
    });

    const result = await response.json();

    if (result.success) {
      alert(`${mcpName} installed! License: ${result.license_key}`);
      // Refresh list
      fetchInstalledMCPs();
    }
  };

  const handleConnect = async (mcpName: string, direction: 'input' | 'output') => {
    await fetch('/api/orchestrator/marketplace/connect', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mcp_name: mcpName, direction })
    });

    // Update UI
  };

  return (
    <div>
      {/* MCP Cards */}
      {mcps.map(mcp => (
        <MCPCard
          key={mcp.id}
          mcp={mcp}
          onInstall={() => handleInstall(mcp.name)}
          onConnect={handleConnect}
        />
      ))}
    </div>
  );
}
```

### Drag & Drop Canvas

```typescript
// Drop zones for Input/Output
<DropZone label="Input (Data Sources)" onDrop={(mcp) => handleConnect(mcp, 'input')}>
  {connectedMCPs.input.map(mcp => <MCPNode name={mcp} />)}
</DropZone>

<DropZone label="Output (Target Systems)" onDrop={(mcp) => handleConnect(mcp, 'output')}>
  {connectedMCPs.output.map(mcp => <MCPNode name={mcp} />)}
</DropZone>
```

## Third-Party Developer Integration

### Register as MCP Developer

```bash
POST /api/mcp-developers/register
{
  "company_name": "AI Solutions GmbH",
  "contact_email": "dev@aisolutions.de",
  "description": "We build AI tools for manufacturing"
}
```

### Submit MCP for Approval

```bash
POST /api/mcp-developers/mcps
{
  "name": "invoice-pro",
  "version": "1.0.0",
  "category": "finance",
  "description": "Advanced invoice OCR",
  "connection_type": "api",
  "api_docs_url": "https://docs.invoice-pro.com",
  "pricing_model": "subscription",
  "monthly_price_cents": 2000
}
```

### Approval Workflow

1. Developer submits MCP → Status: `pending`
2. 0711 Admin reviews → Approves or Rejects
3. If approved → Status: `approved`, visible in marketplace
4. Customers can install

### Revenue Share

- **0711:** 30%
- **Developer:** 70%

Payouts via Stripe Connect.

---

## Core MCPs Reference

### CTAX (Corporate Tax Engine)

**Category:** Finance
**Price:** €500/month
**Connection:** Shared

**Features:**
- VAT calculation
- ELSTER filing
- Tax compliance
- Document analysis

### LAW (Legal Contracts)

**Category:** Legal
**Price:** €500/month
**Connection:** Shared

**Features:**
- Contract analysis
- Risk detection
- Compliance checking
- Legal research

### TENDER (Public Tenders)

**Category:** Operations
**Price:** €500/month
**Connection:** Shared

**Features:**
- Tender analysis
- Response generation
- Qualification check
- Deadline tracking

### ETIM (Product Classification)

**Category:** Logistics
**Price:** €500/month
**Connection:** Shared

**Features:**
- Product classification
- ETIM/ECLASS mapping
- Semantic search
- Feature extraction

### MARKET (Market Intelligence)

**Category:** Marketing
**Price:** €750/month
**Connection:** Shared

**Features:**
- Competitive analysis
- Pricing intelligence
- Market coverage
- Opportunity detection

### PUBLISH (Multi-Channel Publishing)

**Category:** Marketing
**Price:** €750/month
**Connection:** Shared

**Features:**
- E-commerce optimization
- Datasheet generation
- SEO optimization
- Content packs

### SYNDICATE (Distribution)

**Category:** Operations
**Price:** €500/month
**Connection:** Shared

**Features:**
- Partner distribution
- Format conversion
- Automated syndication
- Compliance checking

---

## Best Practices

1. **Install only what you need** - Each MCP has monthly costs
2. **Test connections** - Always test before going live
3. **Use shared MCPs** - More cost-effective than sidecars
4. **Monitor usage** - Track queries and costs
5. **Update regularly** - Keep MCPs up to date

---

**Built with ❤️ by 0711 Intelligence**
