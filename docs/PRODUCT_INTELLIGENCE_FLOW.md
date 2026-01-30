# Product Intelligence Flow

## The Goal

**"Upload products in 10 minutes → Immediately have the right Connectors activated"**

This document explains how the Product Intelligence system makes uploaded data immediately useful.

---

## The Problem (Before)

```
Customer uploads products
        ↓
??? What type of products?
??? What's missing?
??? Which Connectors?
        ↓
Manual configuration
(hours/days)
        ↓
Finally useful
```

---

## The Solution (After)

```
Customer uploads products (any format)
        ↓
┌─────────────────────────────────────────────────────────────────┐
│                   PRODUCT INTELLIGENCE                          │
│                                                                 │
│  1. FIELD DETECTION                                             │
│     • Detect fields: artikelnummer → sku, bezeichnung → title   │
│     • Works with German, English, any naming convention         │
│                                                                 │
│  2. CATEGORY DETECTION                                          │
│     • Analyze product names/descriptions                        │
│     • Detect: ELECTRICAL, AUTOMOTIVE, INDUSTRIAL, etc.          │
│     • Use keyword patterns + Claude for accuracy                │
│                                                                 │
│  3. COMPLETENESS ANALYSIS                                       │
│     • Check: titles ✓, descriptions ⚠️, images ✗, prices ✓     │
│     • Calculate quality scores                                  │
│     • Identify gaps                                             │
│                                                                 │
│  4. CLASSIFICATION DETECTION                                    │
│     • Found ETIM codes? → Already classified!                   │
│     • Found ECLASS codes? → Industrial standard!                │
│     • No codes? → Recommend classification connectors           │
│                                                                 │
│  5. CONNECTOR MAPPING                                           │
│     • Electrical + no ETIM → Enable ETIM connector              │
│     • Missing descriptions → Enable PUBLISH connector           │
│     • Has prices + ETIM → Enable DATANORM export               │
│     • Marketplace ready → Enable Amazon/Shopify                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
        ↓
Connectors AUTO-ENABLED
        ↓
🎉 IMMEDIATELY USEFUL!
```

---

## Connector Auto-Enable Logic

### Input/Enrichment Connectors

| Connector | Auto-enables when | Products applicable |
|-----------|-------------------|---------------------|
| **ETIM** | Electrical/HVAC/Plumbing + <50% ETIM coverage | Products without ETIM |
| **ECLASS** | Industrial/Automotive + <50% ECLASS coverage | Products without ECLASS |
| **PUBLISH** | Any category + <80% description coverage | Products without descriptions |
| **IMAGE-AI** | Any category + <50% image coverage | Products without images |

### Output Connectors

| Connector | Auto-enables when | Products applicable |
|-----------|-------------------|---------------------|
| **DATANORM** | Electrical/Industrial + has prices | All products with prices |
| **BMEcat** | Has classification codes | Classified products |
| **Amazon** | Marketplace readiness >60% | Ready products |
| **Shopify** | Marketplace readiness >60% | Ready products |

---

## Category Detection

### Keywords by Category

```
ELECTRICAL:
  kabel, cable, schalter, switch, stecker, connector,
  sicherung, fuse, led, lampe, lamp, volt, ampere

ELECTRONICS:
  chip, pcb, platine, sensor, display, controller,
  arduino, raspberry, modul, module, usb, hdmi

AUTOMOTIVE:
  auto, car, kfz, fahrzeug, vehicle, motor, engine,
  bremse, brake, reifen, tire, batterie, battery

INDUSTRIAL:
  maschine, machine, werkzeug, tool, pumpe, pump,
  motor, antrieb, drive, ventil, valve, getriebe

HVAC:
  heizung, heating, klima, air, lüftung, ventilation,
  thermostat, wärmepumpe, heat pump, kühlung, cooling

PLUMBING:
  rohr, pipe, fitting, ventil, valve, armatur,
  faucet, sanitär, sanitary, wasser, water
```

---

## Field Detection

The system auto-maps ANY field names to standard fields:

```
Your field          →  Standard field
─────────────────────────────────────────
artikelnummer       →  sku
art_nr              →  sku
item_number         →  sku

bezeichnung         →  title
product_name        →  title
artikel             →  title

beschreibung        →  description
langtext            →  description
description_long    →  description

hersteller          →  brand
manufacturer        →  brand
marke               →  brand

vk_preis            →  price
retail_price        →  price
verkaufspreis       →  price

ean                 →  gtin
gtin13              →  gtin
barcode             →  gtin

etim_class          →  etim
etim_code           →  etim
ec                  →  etim
```

---

## Data Quality Scoring

### Field Importance

| Level | Fields | Weight |
|-------|--------|--------|
| **Critical** | sku, title, price | 60% of score |
| **Important** | description, gtin, brand, image, category | 30% of score |
| **Optional** | etim, eclass, weight, dimensions | 10% of score |

### Marketplace Readiness

Products are "marketplace ready" when:
- Title: 100% present (30% weight)
- Price: 100% present (25% weight)
- Image: >50% present (20% weight)
- GTIN: >80% present (15% weight)
- Description: >50% present (10% weight)

**Score ≥60% = Ready for Amazon, Shopify, etc.**

---

## API Endpoints

### Analyze Products (JSON)
```bash
POST /api/product-intelligence/analyze
Content-Type: application/json

{
  "products": [
    {"artikelnummer": "123", "bezeichnung": "Schalter", "preis": 45.50},
    ...
  ],
  "sample_size": 1000
}
```

### Analyze Products (File Upload)
```bash
POST /api/product-intelligence/analyze-file
Content-Type: multipart/form-data

file: products.csv (or .json, .xlsx)
sample_size: 1000
```

### Get Connector Mapping Rules
```bash
GET /api/product-intelligence/connector-mapping
```

### Enable Connectors
```bash
POST /api/product-intelligence/enable-connectors
Content-Type: application/json

{
  "connector_ids": ["etim", "publish", "datanorm"],
  "customer_id": "cust_123"
}
```

---

## Example Response

```json
{
  "success": true,
  "report": {
    "total_products": 125000,
    "primary_category": "electrical",
    "category_confidence": 0.94,
    
    "overall_completeness": "good",
    "completeness_score": 78.5,
    
    "field_analysis": [
      {"field_name": "sku", "completeness_percent": 100, "importance": "critical"},
      {"field_name": "title", "completeness_percent": 100, "importance": "critical"},
      {"field_name": "price", "completeness_percent": 95, "importance": "critical"},
      {"field_name": "description", "completeness_percent": 45, "importance": "important"},
      {"field_name": "image", "completeness_percent": 62, "importance": "important"},
      {"field_name": "etim", "completeness_percent": 38, "importance": "optional"}
    ],
    
    "recommended_connectors": [
      {
        "connector_id": "etim",
        "connector_name": "ETIM Klassifizierung",
        "reason": "77,500 Produkte können mit ETIM klassifiziert werden",
        "auto_enable": true
      },
      {
        "connector_id": "publish",
        "connector_name": "PUBLISH Beschreibungsgenerator",
        "reason": "68,750 Produkte haben keine/kurze Beschreibungen",
        "auto_enable": true
      },
      {
        "connector_id": "datanorm",
        "connector_name": "DATANORM Export",
        "reason": "DATANORM-Export für Großhandel",
        "auto_enable": true
      }
    ],
    
    "auto_enabled_connectors": ["etim", "publish", "datanorm"],
    
    "data_quality_score": 82.3,
    "marketplace_readiness": 71.5,
    "enrichment_potential": 65.0,
    
    "summary_text": "Sie haben 125,000 Produkte im Bereich Elektrotechnik hochgeladen. Die Datenqualität ist gut (78.5%). Wir haben 5 passende Connectors gefunden, 3 wurden automatisch aktiviert.",
    
    "quick_wins": [
      "ETIM Klassifizierung: 77,500 Produkte können mit ETIM klassifiziert werden",
      "PUBLISH Beschreibungsgenerator: 68,750 Produkte haben keine/kurze Beschreibungen",
      "DATANORM Export: DATANORM-Export für Großhandel"
    ]
  }
}
```

---

## Integration with Smart Onboarding

The Product Intelligence is integrated into the onboarding flow:

```
/onboarding page
      │
      ▼
Step 1: Upload files (CSV, Excel, JSON)
      │
      ▼
Step 2: Product Intelligence analyzes
      │
      ├─► Detect category
      ├─► Analyze completeness
      ├─► Find classifications
      └─► Map to connectors
      │
      ▼
Step 3: Show results + recommendations
      │
      ├─► "You have 125K electrical products"
      ├─► "78% data quality"
      ├─► "3 connectors auto-enabled"
      └─► "€12.5M revenue potential"
      │
      ▼
Step 4: One-click deploy
      │
      ├─► Import products to lakehouse
      ├─► Enable recommended connectors
      ├─► Start AI training
      └─► Activate chat
      │
      ▼
🎉 Customer can chat about their products!
```

---

## The "10 Minute Promise"

1. **0:00** - Customer opens onboarding
2. **0:30** - Drags product file(s) into upload zone
3. **1:00** - Files uploaded
4. **3:00** - AI analysis complete, shows report
5. **3:30** - Customer reviews recommendations
6. **4:00** - Clicks "Deploy All"
7. **8:00** - Products imported, connectors enabled
8. **10:00** - 🎉 Customer asks first question in chat

**That's the goal. Upload → Analyze → Deploy → Chat. 10 minutes.**
