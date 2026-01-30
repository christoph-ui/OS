# Onboarding System Architecture

**Updated:** 2026-01-30

## Two Parallel Onboarding Tracks

### 1. Traditional Onboarding (7-step wizard)
**Location:** `/apps/website/app/onboarding/page.tsx`

Steps:
1. Welcome
2. Company Info
3. Data Upload
4. MCP Selection
5. Connectors
6. Processing
7. Completion

### 2. Smart Onboarding (AI-powered, 4-step)
**Location:** `/console/frontend/src/app/onboarding/page.tsx`

Steps:
1. Upload
2. AI Analysis
3. Results
4. Deploy

---

## Concierge Agent

**Location:** `/agents/concierge/agent.py`

### Core Responsibilities
- Guides customers through onboarding conversationally
- Analyzes uploaded files (BMECat, ETIM, DATANORM, CSV, Excel, PDF, ZIP)
- Generates connector recommendations
- Collects credentials securely
- Creates "Context Briefs" for Import Agent handoff

### 9 Onboarding Stages
1. `WELCOME`
2. `COMPANY_PROFILE`
3. `DATA_UPLOAD`
4. `DATA_ANALYSIS`
5. `CONNECTOR_SUGGESTIONS`
6. `CREDENTIALS`
7. `IMPORT_HANDOFF`
8. `MONITORING`
9. `COMPLETE`

### File Type Intelligence
- Detects B2B formats (BMECat XML, ETIM, DATANORM)
- Analyzes data quality and completeness
- Identifies business model:
  - B2B Distributor
  - B2B Manufacturer
  - B2C Retailer
  - Marketplace
- Generates field mappings and value projections

---

## State Management

### Database Model (`/api/models/customer.py`)
```python
onboarding_status: not_started → plan_selected → payment_completed → data_uploaded → completed
onboarding_step: str  # Current step identifier
onboarding_data: JSONB  # Plans, MCPs, connectors
onboarding_completed_at: datetime
```

### In-Memory Sessions
```python
wizard_sessions: dict[str, OnboardingWizard] = {}  # Redis in production
```

---

## API Architecture

**17 Onboarding Endpoints across 3 route files:**

### Traditional Routes (`/api/routes/onboarding.py`)
- Company info, plan selection, MCP/connector config
- Deployment triggering & status polling
- Available MCPs/connectors discovery

### Wizard Routes (`/api/routes/onboarding_wizard.py`)
- Session management (start, next, previous, submit)
- File upload with analysis
- Chat interaction
- Import job tracking

### Smart Routes (`/api/routes/intelligent_onboarding.py`)
- AI-powered upload & analysis
- Field mapping confirmation
- ROI projection
- One-click deployment

---

## AI-Powered Intelligence

### DataDiscoveryAgent (`/api/services/intelligent_onboarding_service.py`)

Uses **Claude Sonnet 4.5** for analysis:
- Detects business models automatically
- Calculates data quality scores (0-100)
- Projects revenue opportunities & cost savings
- Recommends connectors with reasoning

### Analysis Output
- File analyses with data type detection
- Product count & completeness metrics
- ETIM/GTIN/image coverage
- Language detection
- Field mapping suggestions
- Value projections

---

## Context Brief Handoff

The concierge creates a comprehensive brief for the Import Agent:

```python
ContextBrief:
  - Company profile & business type
  - Uploaded files with analysis
  - Data quality flags (ETIM codes, GTIN, images)
  - Field mapping hints
  - Target channels & priority connectors
  - Special notes from concierge
```

This enables intelligent import processing without re-analyzing data.

---

## End-to-End Flow Example

### B2B Distributor Journey

1. Enter company info (Acme GmbH, Elektro)
2. Upload files (BMECat XML, Excel, images ZIP)
3. Concierge analyzes: 12,450 products, ETIM present, 4,130 missing images
4. Recommends: DATANORM Export, ETIM Enrichment, Amazon SP-API
5. Select MCPs → Calculate pricing (€13,800/month)
6. Provide Amazon credentials
7. Deploy → Real-time WebSocket updates
8. Context Brief → Import Agent begins
9. Verification checks (12,450 files, 8 containers running)
10. Success screen with Console URL

---

## Files Reference

| Component | Location | Lines |
|-----------|----------|-------|
| Concierge Agent | `agents/concierge/agent.py` | 1-890 |
| Wizard UI | `agents/concierge/wizard.py` | 1-450 |
| Smart Analysis | `api/services/intelligent_onboarding_service.py` | 1-650 |
| Traditional UI | `apps/website/app/onboarding/page.tsx` | 1-1200 |
