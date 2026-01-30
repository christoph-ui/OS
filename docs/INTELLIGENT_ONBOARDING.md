# Intelligent Zero-Config Onboarding

## The Vision

**"Dump your data. We figure out the rest."**

For a platform with 1000+ B2B clients (automotive, electronics) with hundreds of thousands of products, onboarding must be:

1. **Dummy-proof** - No technical knowledge required
2. **Self-adapting** - System learns from any data format
3. **Value-first** - Show business impact within minutes
4. **Connector-driven** - Automatically suggest relevant connectors

---

## Current State Assessment

### What Exists ✓
- Claude-powered handler generation for unknown formats
- Rule-based + LLM classification
- Smart chunking and embedding
- Intelligent extraction to standard schemas
- Data value report generator
- Basic onboarding flow (6 steps)

### What's Missing ✗
- **Data Discovery Agent** - Auto-detect what's in uploaded data
- **Business Model Detector** - Understand if B2B, B2C, marketplace, distributor
- **Schema Mapper** - Auto-map any format to standard schemas
- **Connector Recommender** - Suggest connectors based on data analysis
- **Value Calculator** - Instant ROI/opportunity projection
- **Guided Configuration** - AI explains decisions in plain language

---

## New Architecture: Intelligent Onboarding Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    INTELLIGENT ONBOARDING FLOW                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   STEP 1               STEP 2               STEP 3               STEP 4    │
│   ────────             ────────             ────────             ────────   │
│   UPLOAD               ANALYZE              CONFIGURE            ACTIVATE  │
│                                                                             │
│   ┌─────────┐         ┌─────────┐          ┌─────────┐         ┌─────────┐ │
│   │ 📁      │         │ 🔍      │          │ ⚙️      │         │ 🚀      │ │
│   │ Drop    │────────►│ AI      │─────────►│ Auto    │────────►│ Go      │ │
│   │ Files   │         │ Analyzes│          │ Config  │         │ Live    │ │
│   └─────────┘         └─────────┘          └─────────┘         └─────────┘ │
│                                                                             │
│   • Any format         • Detect format      • Map fields        • Connect  │
│   • Drag & drop        • Detect business    • Suggest MCPs      • Process  │
│   • Bulk upload        • Sample analysis    • Show value        • Chat     │
│   • API push           • Schema discovery   • Confirm           • Deploy   │
│                                                                             │
│   ─────────────────────────────────────────────────────────────────────────│
│   TIME: 30 seconds     TIME: 2-5 minutes    TIME: 1 click      INSTANT     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Components

### 1. Data Discovery Agent

Automatically analyzes uploaded files to understand:

```python
class DataDiscoveryAgent:
    """
    AI agent that analyzes uploaded data to understand:
    - What kind of data (products, customers, orders, documents)
    - Data format (CSV, JSON, XML, Excel, proprietary)
    - Data quality (completeness, consistency)
    - Business context (B2B, B2C, distributor, manufacturer)
    - Product categories (electronics, automotive, industrial)
    """
    
    async def analyze(self, files: List[UploadedFile]) -> DataDiscoveryReport:
        # Sample first N rows of each file
        # Use Claude to understand structure
        # Detect business model from data patterns
        # Return comprehensive report
```

**Output Example:**
```json
{
  "summary": {
    "total_files": 47,
    "total_records": 125000,
    "data_types": ["products", "pricing", "images", "specs"],
    "formats": {"csv": 12, "json": 5, "xlsx": 30},
    "languages": ["de", "en", "fr"],
    "quality_score": 87
  },
  "business_model": {
    "type": "B2B_DISTRIBUTOR",
    "confidence": 0.94,
    "indicators": [
      "GTIN/EAN present in 98% of products",
      "Manufacturer fields populated",
      "Wholesale pricing structure detected",
      "ETIM/ECLASS codes found"
    ]
  },
  "product_analysis": {
    "total_products": 125000,
    "categories": {
      "electrical_components": 45000,
      "automation_systems": 32000,
      "cables_connectors": 28000,
      "other": 20000
    },
    "completeness": {
      "title": "100%",
      "description": "78%",
      "price": "95%",
      "images": "62%",
      "specs": "45%"
    }
  },
  "recommendations": {
    "immediate_value": [
      {
        "connector": "ETIM",
        "reason": "45,000 products match ETIM categories",
        "value": "Auto-classify 45K products instantly"
      },
      {
        "connector": "PUBLISH",
        "reason": "Missing descriptions can be generated",
        "value": "Complete 22% missing descriptions"
      }
    ],
    "output_channels": [
      {"connector": "shopify", "products_ready": 78000},
      {"connector": "amazon-sp", "products_ready": 65000},
      {"connector": "datanorm", "products_ready": 95000}
    ]
  }
}
```

### 2. Business Model Detector

```python
class BusinessModelDetector:
    """
    Detects business model from data patterns:
    - B2B Distributor (bulk products, tiered pricing)
    - B2B Manufacturer (own brand, technical specs)
    - B2C Retailer (consumer products, marketing focus)
    - Marketplace Seller (multi-brand, competitive pricing)
    """
    
    INDICATORS = {
        "B2B_DISTRIBUTOR": [
            "Multiple manufacturers",
            "Wholesale/tiered pricing",
            "GTIN/EAN codes",
            "ETIM/ECLASS classification",
            "Technical datasheets"
        ],
        "B2B_MANUFACTURER": [
            "Single brand dominance",
            "CAD/3D models",
            "Spare parts relationships",
            "Certification documents"
        ],
        "B2C_RETAILER": [
            "Consumer-focused descriptions",
            "Marketing images",
            "Review mentions",
            "Seasonal products"
        ]
    }
```

### 3. Schema Mapper

Auto-maps ANY input format to standard lakehouse schemas:

```python
class IntelligentSchemaMapper:
    """
    Uses Claude to map arbitrary fields to standard schemas.
    
    Input: {"Artikelnummer": "123", "Bezeichnung": "Schalter", "VK-Preis": 12.50}
    Output: {"sku": "123", "title": "Schalter", "price": 12.50}
    
    Also generates transformation rules that are saved for future imports.
    """
    
    async def create_mapping(
        self,
        sample_data: List[dict],
        target_schema: str = "products"
    ) -> FieldMapping:
        """
        1. Analyze sample data structure
        2. Use Claude to understand field meanings
        3. Generate mapping to standard schema
        4. Create transformation functions
        5. Validate on sample
        6. Return mapping for approval
        """
```

### 4. Value Calculator

Instant ROI projection based on data analysis:

```python
class ValueCalculator:
    """
    Calculates business value from data:
    - Revenue opportunity (channels × products × avg_price)
    - Cost savings (automation potential)
    - Time savings (manual work eliminated)
    - Competitive advantage (speed to market)
    """
    
    async def calculate(self, discovery: DataDiscoveryReport) -> ValueReport:
        # Calculate channel expansion opportunity
        channels = len(discovery.recommendations.output_channels)
        products = discovery.product_analysis.total_products
        
        # Revenue opportunity
        revenue_multiplier = min(channels * 0.3, 5)  # Conservative
        
        # Cost savings
        content_generation_savings = discovery.product_analysis.missing_descriptions * 50  # €50/description
        
        return ValueReport(
            revenue_opportunity=f"€{products * 100 * revenue_multiplier:,.0f}",
            cost_savings=f"€{content_generation_savings:,.0f}",
            time_to_value="24 hours"
        )
```

---

## New Onboarding API Endpoints

```python
# Step 1: Upload & Auto-Analyze
POST /api/onboarding/upload
# Returns: Upload ID, starts background analysis

GET /api/onboarding/{upload_id}/analysis
# Returns: DataDiscoveryReport (as above)

# Step 2: Review & Confirm Mapping
GET /api/onboarding/{upload_id}/mapping
# Returns: Proposed field mappings, connector recommendations

POST /api/onboarding/{upload_id}/mapping/confirm
# Body: {"confirmed": true, "adjustments": [...]}

# Step 3: Value Preview
GET /api/onboarding/{upload_id}/value
# Returns: ValueReport with ROI projections

# Step 4: One-Click Deploy
POST /api/onboarding/{upload_id}/deploy
# Starts deployment, returns stream of progress

GET /api/onboarding/{upload_id}/status
# Returns: Deployment progress, ETA
```

---

## UI Flow (Dummy-Proof)

### Screen 1: Upload
```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│     📁 Daten hochladen                                       │
│                                                              │
│     ┌────────────────────────────────────────────────────┐   │
│     │                                                    │   │
│     │      Dateien hier ablegen                          │   │
│     │      oder klicken zum Auswählen                    │   │
│     │                                                    │   │
│     │      CSV, Excel, JSON, XML, PDF...                 │   │
│     │      Beliebige Formate werden unterstützt          │   │
│     │                                                    │   │
│     └────────────────────────────────────────────────────┘   │
│                                                              │
│     Bereits hochgeladen:                                     │
│     ✅ produktkatalog.xlsx (125.000 Produkte)               │
│     ✅ preisliste_2024.csv (125.000 Preise)                 │
│     ⏳ bilder.zip (wird analysiert...)                       │
│                                                              │
│     [Weiter →]                                               │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Screen 2: AI Analysis (Auto)
```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│     🔍 Ihre Daten werden analysiert...                       │
│                                                              │
│     ████████████████░░░░░░░░░░░░  68%                       │
│                                                              │
│     ✅ Format erkannt: Excel, CSV                            │
│     ✅ 125.000 Produkte gefunden                             │
│     ✅ Geschäftsmodell: B2B Distributor                      │
│     ⏳ Felder werden zugeordnet...                           │
│                                                              │
│     💡 Was wir herausgefunden haben:                         │
│                                                              │
│     "Sie sind ein B2B-Distributor für Elektrotechnik mit     │
│      125.000 Produkten von 47 Herstellern. Ihre Daten        │
│      enthalten ETIM-Klassifizierungen, was perfekt für       │
│      automatische Marktplatz-Integration ist."               │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Screen 3: Value Preview
```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│     💰 Ihr Potenzial                                         │
│                                                              │
│     ┌────────────────┐  ┌────────────────┐                  │
│     │                │  │                │                  │
│     │   €12.5M       │  │   €450K        │                  │
│     │   Umsatz-      │  │   Kosten-      │                  │
│     │   potenzial    │  │   ersparnis    │                  │
│     │                │  │                │                  │
│     └────────────────┘  └────────────────┘                  │
│                                                              │
│     Empfohlene Connectors:                                   │
│                                                              │
│     ✅ ETIM Klassifizierung                                  │
│        45.000 Produkte automatisch klassifizieren            │
│                                                              │
│     ✅ PUBLISH Multi-Channel                                 │
│        Beschreibungen für 28.000 Produkte generieren         │
│                                                              │
│     ✅ Amazon, eBay, Shopify                                 │
│        78.000 Produkte sofort listbar                        │
│                                                              │
│     [Alles aktivieren →]                                     │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Screen 4: Done
```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│     🎉 Fertig!                                               │
│                                                              │
│     Ihre Daten sind bereit. Chatten Sie los!                 │
│                                                              │
│     ┌────────────────────────────────────────────────────┐   │
│     │ 💬 Fragen Sie mich etwas...                        │   │
│     │                                                    │   │
│     │ "Welche Produkte verkaufen sich am besten?"        │   │
│     │ "Erstelle eine Amazon-Listing für Artikel 12345"   │   │
│     │ "Wie viele Produkte haben keine Bilder?"           │   │
│     └────────────────────────────────────────────────────┘   │
│                                                              │
│     Nächste Schritte:                                        │
│     • Amazon-Konto verbinden                                 │
│     • Beschreibungen generieren lassen                       │
│     • DATEV-Export einrichten                                │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## Implementation Priority

### Phase 1: Data Discovery Agent (Week 1)
- [ ] Build `DataDiscoveryAgent` class
- [ ] Claude prompt for data understanding
- [ ] Business model detection
- [ ] Basic UI flow

### Phase 2: Schema Mapper (Week 2)
- [ ] Build `IntelligentSchemaMapper`
- [ ] Field mapping with Claude
- [ ] Transformation rule generation
- [ ] Mapping UI with preview

### Phase 3: Value Calculator (Week 3)
- [ ] Build `ValueCalculator`
- [ ] ROI projection models
- [ ] Connector recommendation engine
- [ ] Value preview UI

### Phase 4: One-Click Deploy (Week 4)
- [ ] Streamlined deployment
- [ ] Progress streaming
- [ ] Instant chat access
- [ ] Post-onboarding guide

---

## Technical Implementation

See `api/services/intelligent_onboarding_service.py` for full implementation.
