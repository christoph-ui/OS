# 0711 Agent Architecture

## Overview

The 0711 platform uses a multi-agent system for intelligent onboarding and data processing.

```
┌─────────────────────────────────────────────────────────────────────┐
│                       CUSTOMER ONBOARDING FLOW                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  👤 Customer                                                         │
│       │                                                              │
│       ▼                                                              │
│  ┌──────────────────┐                                                │
│  │   CONCIERGE      │  The Friendly Wizard                          │
│  │     AGENT        │  - Speaks business language                   │
│  │                  │  - Guides data upload                         │
│  │  "Upload your    │  - Analyzes files                             │
│  │   products,      │  - Suggests connectors                        │
│  │   I'll help!"    │  - Manages credentials                        │
│  └────────┬─────────┘  - Creates Context Brief                      │
│           │                                                          │
│           │  Context Brief (handoff document):                       │
│           │  ┌─────────────────────────────────┐                    │
│           │  │ • Customer profile              │                    │
│           │  │ • Business type (B2B/B2C)       │                    │
│           │  │ • Uploaded files + analysis     │                    │
│           │  │ • Data quality assessment       │                    │
│           │  │ • Target channels               │                    │
│           │  │ • Field mapping hints           │                    │
│           │  │ • Special instructions          │                    │
│           │  └─────────────────────────────────┘                    │
│           │                                                          │
│           ▼                                                          │
│  ┌──────────────────┐                                                │
│  │    IMPORT        │  The Data Specialist                          │
│  │     AGENT        │  - Speaks data formats                        │
│  │                  │  - Parses BMECat, CSV, etc.                   │
│  │  "I'll map       │  - Maps to 0711 schema                        │
│  │   everything     │  - Classifies products                        │
│  │   to our         │  - Enriches missing data                      │
│  │   schema."       │  - Validates & loads                          │
│  └────────┬─────────┘                                                │
│           │                                                          │
│           ▼                                                          │
│  ┌──────────────────┐                                                │
│  │    LAKEHOUSE     │  Unified Product Data                         │
│  │                  │  - Consistent schema                          │
│  │                  │  - Ready for MCPs                             │
│  │                  │  - Classification codes                       │
│  └──────────────────┘                                                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Agents

### 1. Concierge Agent (`agents/concierge/`)

**Role:** The friendly onboarding wizard that guides customers.

**Responsibilities:**
- Welcome and guide customers through setup
- Collect company profile information
- Handle file uploads and initial analysis
- Explain what the data contains in business terms
- Suggest relevant connectors based on data
- Collect and securely store credentials
- Create a "Context Brief" for the Import Agent
- Monitor import progress and explain results

**Speaks:** Business language, German/English

**Files:**
- `agent.py` - Main agent logic
- `wizard.py` - Wizard UI/conversation layer

### 2. Import Agent (`agents/import_agent/`)

**Role:** The data processing specialist.

**Responsibilities:**
- Receive Context Brief from Concierge
- Parse product files (BMECat, ETIM, CSV, Excel)
- Detect field mappings automatically
- Map ALL fields to 0711 unified schema
- Classify products into 0711 category structure
- Enrich missing data (ETIM codes, descriptions)
- Validate data quality
- Load to Lakehouse

**Speaks:** Data formats, schemas, classification systems

**Files:**
- `agent.py` - Main import logic
- `parsers.py` - Format-specific parsers
- `schema_mapper.py` - Field mapping logic

## Context Brief

The key handoff document between agents. Contains everything the Import Agent needs to know.

```python
@dataclass
class ContextBrief:
    brief_id: UUID
    customer_id: UUID
    
    # Customer context
    company_name: str
    business_type: BusinessType  # b2b_distributor, manufacturer, etc.
    industry: str
    
    # Data context
    files: List[UploadedFile]
    has_etim_codes: bool
    has_gtin: bool
    has_images: bool
    
    # Mapping hints
    field_mapping_hints: Dict[str, str]  # source_field -> target_field
    
    # Goals
    target_channels: List[str]  # datanorm, amazon, etc.
    priority_connectors: List[str]
    
    # Free-text instructions
    notes: str
```

## 0711 Unified Schema

ALL product data maps to this single schema, regardless of source format.

### Core Fields

| Field | Type | Description |
|-------|------|-------------|
| `sku` | string | Customer's article number |
| `gtin` | string | EAN/GTIN/UPC |
| `name` | string | Product name |
| `description_short` | string | Short description |
| `description_long` | string | Full description |
| `category_id` | string | 0711 category ID |
| `etim_class` | string | ETIM classification (preserved) |
| `eclass_code` | string | ECLASS code (preserved) |
| `price_net` | float | Net price |
| `images` | list | Image paths/URLs |

### Why Unified Schema?

1. **Consistent MCPs** - Connectors always get the same structure
2. **Easy Export** - DATANORM, BMECat, marketplaces all work
3. **No Data Loss** - Original codes preserved as metadata
4. **Classification Agnostic** - ETIM, ECLASS, custom all supported

## Supported Input Formats

### BMECat XML
- Versions: 1.0, 1.2, 2005
- Auto-detected from file content
- Full feature extraction

### CSV/Excel
- Auto-detect delimiter (`,`, `;`, `\t`)
- Auto-detect encoding (UTF-8, Latin-1, CP1252)
- Intelligent field name matching

### ETIM Pricelist
- Version 9.0+ supported
- Classification codes extracted

### DATANORM
- Versions 4.0, 5.0
- Full article and price extraction

## API Endpoints

### Wizard Flow

```
POST   /api/onboarding-wizard/start           # Start wizard
GET    /api/onboarding-wizard/{id}/state      # Get current state
POST   /api/onboarding-wizard/{id}/next       # Next step
POST   /api/onboarding-wizard/{id}/submit     # Submit step data
POST   /api/onboarding-wizard/{id}/upload     # Upload file
POST   /api/onboarding-wizard/{id}/chat       # Chat with agent
POST   /api/onboarding-wizard/{id}/start-import  # Begin import
GET    /api/onboarding-wizard/{id}/import-status # Check progress
```

## Usage Example

```python
from agents.concierge import ConciergeAgent, OnboardingWizard
from agents.import_agent import ImportAgent

# Start wizard
wizard = OnboardingWizard(customer_id)

# Customer uploads file
result = await wizard.upload_file("catalog.xml", content)
# Returns: analysis, suggestions

# Customer selects connectors, provides credentials
await wizard.submit_step({"selected_connectors": ["datanorm", "amazon"]})

# Start import - creates Context Brief and hands off
brief = wizard.agent._create_context_brief()

# Import Agent takes over
import_agent = ImportAgent()
progress = await import_agent.process_import(brief.to_dict(), files)

# Progress tracked, results loaded to lakehouse
print(f"Imported: {progress.successful_records}")
print(f"Needs review: {progress.needs_review}")
```

## Key Design Decisions

1. **Two Agents, Clear Separation**
   - Concierge speaks business, Import speaks data
   - Clean handoff via Context Brief

2. **Always Map to Unified Schema**
   - No matter what format comes in
   - MCPs can rely on consistent structure

3. **Preserve Original Codes**
   - ETIM, ECLASS kept as metadata
   - Can export in any format needed

4. **LLM-Assisted but Not Required**
   - Pattern matching handles 90% of cases
   - LLM helps with edge cases

5. **Streaming Progress**
   - Real-time updates to customer
   - Concierge explains what's happening
