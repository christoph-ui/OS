# 🤖 Intelligente Daten-Ingestion - Komplette Erklärung

**Datum**: 2026-01-28
**Status**: ✅ **Produktiv & KI-Powered**

---

## 🎯 Überblick

Die 0711 Platform hat einen **sophistizierten KI-gesteuerten Ingestion-Prozess**, der:
1. **Jedes Dateiformat** automatisch erkennt und verarbeitet
2. **Dynamisch klassifiziert** (Tax, Legal, Products, HR, etc.)
3. **Intelligent extrahiert** (strukturierte Daten → SQL, Entities → Graph, Text → Vektor)
4. **Due Diligence** durchführt (Datenqualität, Vollständigkeit, Anomalien)
5. **Custom Handlers generiert** (für unbekannte Formate via Claude)

**Kern**: **Claude Sonnet 4.5** analysiert und entscheidet automatisch!

---

## 🏗️ Die 6 Intelligenz-Stufen

```
Datei hochgeladen
    ↓
┌─────────────────────────────────────────────────────────────┐
│  STUFE 1: ADAPTIVE HANDLER GENERATION                       │
│  ─────────────────────────────────────────────────────────  │
│  Unbekanntes Format (.DAT, .proprietary)?                   │
│  → Claude analysiert Struktur                               │
│  → Generiert Python Handler (on-the-fly!)                   │
│  → Validiert & testet Handler                               │
│  → Registriert für zukünftige Nutzung                       │
│                                                             │
│  File: ingestion/claude_handler_generator.py                │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│  STUFE 2: DOCUMENT CLASSIFICATION                           │
│  ─────────────────────────────────────────────────────────  │
│  Zwei-stufig:                                               │
│  1. Rule-Based (schnell, Pattern Matching)                  │
│     → 100+ Keywords (DE/EN) pro Kategorie                   │
│     → Scoring-System                                        │
│  2. Claude Classification (wenn unsicher)                   │
│     → Liest Filename + Content-Sample                       │
│     → Entscheidet: tax/legal/products/hr/general            │
│                                                             │
│  Files: ingestion/classifier/document_classifier.py         │
│         ingestion/classifier/rules.py                       │
│         ingestion/classifier/prompts.py                     │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│  STUFE 3: SCHEMA ANALYSIS (Intelligente Struktur-Erkennung) │
│  ─────────────────────────────────────────────────────────  │
│  Claude analysiert Daten-Struktur:                          │
│  1. Ist das strukturierte Daten? → SQL-Tabellen (Delta)     │
│  2. Gibt es Entities? → Graph-Schema (Neo4j)                │
│  3. Was soll durchsuchbar sein? → Vector-Indices (Lance)    │
│                                                             │
│  Output: StorageStrategy {                                  │
│    data_type: "structured_catalog",                         │
│    sql_tables: [{name, columns, primary_key}],              │
│    graph_schema: {nodes, relationships},                    │
│    vector_indices: [{name, fields}]                         │
│  }                                                          │
│                                                             │
│  File: ingestion/analyzer/schema_analyzer.py                │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│  STUFE 4: INTELLIGENT EXTRACTION                            │
│  ─────────────────────────────────────────────────────────  │
│  Liest DEPLOYMENT.md (Customer Context):                    │
│  - Company: "EATON"                                         │
│  - Industry: "Electrical Components"                        │
│  - Source Format: "BMEcat 2005 XML"                         │
│  - Transformation Rules: {JSONPath → SQL Column}            │
│                                                             │
│  Claude extrahiert mit Context:                             │
│  - Versteht Branchen-Spezifika                              │
│  - Wendet Transformation Rules an                           │
│  - Mapped zu Standard-Schema                                │
│  - Validiert Datenqualität                                  │
│                                                             │
│  Output: Strukturierte Records für Delta Tables             │
│                                                             │
│  File: ingestion/extractor/intelligent_extractor.py         │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│  STUFE 5: ENTITY EXTRACTION (Graph Intelligence)            │
│  ─────────────────────────────────────────────────────────  │
│  Extrahiert Entities für Neo4j:                             │
│  - Companies (Lieferanten, Kunden, Partner)                 │
│  - Products (mit Beziehungen)                               │
│  - People (Ansprechpartner)                                 │
│  - Locations (Standorte)                                    │
│  - Relationships (liefert_an, arbeitet_bei, etc.)           │
│                                                             │
│  Nutzt: spaCy DE + Custom Rules                             │
│                                                             │
│  File: ingestion/processor/entity_extractor.py              │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│  STUFE 6: DUE DILIGENCE & QUALITY CHECKS                    │
│  ─────────────────────────────────────────────────────────  │
│  Claude prüft automatisch:                                  │
│  ✓ Vollständigkeit (alle Pflichtfelder?)                    │
│  ✓ Konsistenz (Preise plausibel? Daten widerspruchsfrei?)  │
│  ✓ Anomalien (Outlier, verdächtige Werte)                   │
│  ✓ Duplikate (gleiche Produkte mehrfach?)                   │
│  ✓ Referenz-Integrität (verweisen IDs auf existierende?)    │
│                                                             │
│  Output: Data Quality Report                                │
│  {                                                          │
│    "completeness_score": 0.95,                              │
│    "missing_fields": ["price: 12 records"],                 │
│    "anomalies": ["Product X has price 0"],                  │
│    "duplicates": 3,                                         │
│    "recommendation": "Ready for production"                 │
│  }                                                          │
│                                                             │
│  File: ingestion/analyzer/schema_analyzer.py (validate)     │
└─────────────────────────────────────────────────────────────┘
```

---

## 📝 Beispiel: EATON Upload

### Input
```
Dateien:
- eaton_products.xml (BMEcat 2005)
- technical_specs.pdf
- unknown_format.DAT (proprietär!)
```

### Prozess

**1. Adaptive Handler Generation**
```
unknown_format.DAT encountered
  ↓
Claude analyzes first 4KB:
  - Encoding: ISO-8859-1
  - Structure: Tab-delimited
  - Columns: ID, Name, Price, Category
  ↓
Generates Python Handler:
  class EatonDatHandler(BaseHandler):
      def extract(self, path):
          # Parse tab-delimited
          # Return structured data
  ↓
Validates syntax (AST)
Tests on sample file
Registers: ".dat" → EatonDatHandler
✓ Ready to process all .DAT files
```

**2. Document Classification**
```
eaton_products.xml
  ↓
Rule-Based Check:
  - Filename contains "produkt" → 80% products
  - Extension .xml → neutral
  - Confidence: 0.8 (above threshold)
  ↓
Classification: "products" ✓

technical_specs.pdf
  ↓
Rule-Based uncertain (generic filename)
  ↓
Claude Classification:
  Sample: "Technical Specifications..."
  Claude: "This is a products document (technical specs)"
  ↓
Classification: "products" ✓
```

**3. Schema Analysis**
```
eaton_products.xml analyzed
  ↓
Claude determines:
  Data Type: STRUCTURED_CATALOG
  ↓
  SQL Tables:
    - products (gtin, brand, model, price, ...)
    - suppliers (name, id, contact)
    - categories (etim_class, description)
  ↓
  Graph Schema:
    Nodes: [Product, Supplier, Category]
    Relationships: [
      (Product)-[SUPPLIED_BY]->(Supplier),
      (Product)-[IN_CATEGORY]->(Category)
    ]
  ↓
  Vector Indices:
    - product_descriptions (for search)
    - technical_specs (for RAG)
```

**4. Intelligent Extraction**
```
Reads DEPLOYMENT.md:
  Company: EATON
  Industry: Electrical Components
  Source Format: BMEcat 2005 XML
  Transformation Rules:
    - ARTICLE/ARTICLE_DETAILS/MANUFACTURER_AID → sku
    - ARTICLE/ARTICLE_DETAILS/DESCRIPTION_SHORT → name
    - ARTICLE_PRICE_DETAILS/ARTICLE_PRICE → price
    ...
  ↓
Claude extracts with rules:
  <ARTICLE>
    <ARTICLE_DETAILS>
      <MANUFACTURER_AID>123456</MANUFACTURER_AID>
      <DESCRIPTION_SHORT>Circuit Breaker</DESCRIPTION_SHORT>
    </ARTICLE_DETAILS>
  </ARTICLE>
  ↓
  Mapped to:
  {
    "sku": "123456",
    "name": "Circuit Breaker",
    "gtin": "...",
    "price": 45.99,
    ...
  }
  ↓
Output: 669 product records (validated)
```

**5. Entity Extraction**
```
From extracted products:
  ↓
Entities found:
  - Companies: ["EATON", "Schneider Electric", "ABB"]
  - Products: 669 items
  - Categories: ["Circuit Breakers", "Contactors", ...]
  ↓
Relationships:
  - (Product ID=123)-[MANUFACTURED_BY]->(EATON)
  - (Product ID=123)-[IN_CATEGORY]->(Circuit Breakers)
  - (EATON)-[COMPETES_WITH]->(Schneider Electric)
  ↓
Neo4j Graph: 1,500 nodes, 4,500 edges
```

**6. Due Diligence**
```
Claude validates:
  ✓ Completeness: 98% (12 products missing price)
  ✓ Consistency: Price range €5-€5,000 (plausible)
  ⚠ Anomalies: 3 products with price €0 (flag for review)
  ✓ Duplicates: None found
  ✓ References: All category IDs valid
  ↓
Quality Score: 9.2/10
Recommendation: "Ready for production. Review 3 zero-price items."
  ↓
Report saved to lakehouse
Admin kann Due Diligence Report einsehen
```

---

## 🔧 Technische Komponenten

### 1. Claude Handler Generator
**File**: `ingestion/claude_handler_generator.py`

**Macht**:
- Analysiert unbekannte Dateiformate
- Generiert Python-Code für Handler-Klasse
- Validiert mit AST (Syntax-Check)
- Testet Handler auf Sample-File
- Registriert für zukünftige Nutzung

**Beispiel**: EATON .DAT Format
```python
# Automatisch generiert von Claude:
class EatonDatHandler(BaseHandler):
    async def extract(self, path: Path) -> Optional[str]:
        with open(path, 'r', encoding='iso-8859-1') as f:
            lines = f.readlines()

        header = lines[0].strip().split('\t')
        records = []

        for line in lines[1:]:
            values = line.strip().split('\t')
            record = dict(zip(header, values))
            records.append(record)

        return json.dumps(records)
```

### 2. Document Classifier
**File**: `ingestion/classifier/document_classifier.py`

**Strategie** (2-stufig):
```python
async def classify(file_path, content_sample):
    # Stufe 1: Rule-Based (schnell, kostenlos)
    category, confidence = rule_classifier.classify(file_path)

    if confidence >= 0.6:
        return category  # Sicher genug

    # Stufe 2: Claude Classification (genau, kostet Tokens)
    if content_sample and claude_client:
        prompt = build_classification_prompt(filename, content_sample)
        category = await claude_classify(prompt)
        return category

    # Fallback
    return "general"
```

**Kategorien**:
- `tax` - Steuer, Buchhaltung, DATEV
- `legal` - Verträge, Rechnungen, Compliance
- `products` - Kataloge, ETIM, Stammdaten
- `hr` - Personal, Bewerbungen, Gehaltsabrechnungen
- `general` - Alles andere

### 3. Schema Analyzer
**File**: `ingestion/analyzer/schema_analyzer.py`

**Entscheidet Storage-Strategie**:
```python
await schema_analyzer.analyze(file, content, classification)
  ↓
Returns: StorageStrategy {
    data_type: STRUCTURED_CATALOG,

    sql_tables: [
        TableSchema(
            name="products",
            columns=[
                {name: "gtin", type: "VARCHAR(14)", description: "..."},
                {name: "brand", type: "VARCHAR(100)", ...},
                {name: "price", type: "DECIMAL(10,2)", ...}
            ],
            primary_key="gtin"
        ),
        TableSchema(name="suppliers", ...)
    ],

    graph_schema: GraphSchema(
        nodes=[{type: "Product", properties: [...]}],
        relationships=[{from: "Product", to: "Supplier", type: "SUPPLIED_BY"}]
    ),

    vector_indices: [
        VectorIndex(
            name="product_search",
            fields=["name", "description", "technical_specs"]
        )
    ],

    confidence: "high"
}
```

**Claude Prompt** (vereinfacht):
```
Analyze this data structure:
File: eaton_products.xml
Sample: <ARTICLE>...</ARTICLE>

Determine:
1. Is this structured data for SQL tables?
2. What entities exist for graph database?
3. What text fields need vector indexing?

Return JSON with table schemas, graph schema, vector indices.
```

### 4. Intelligent Extractor
**File**: `ingestion/extractor/intelligent_extractor.py`

**Nutzt Deployment Context**:
```python
# Liest DEPLOYMENT.md (Customer-spezifisch)
deployment_context = {
    "company_name": "EATON",
    "industry": "Electrical Components",
    "source_format": "BMEcat 2005",
    "transformation_rules": {
        "ARTICLE/MANUFACTURER_AID": "sku",
        "ARTICLE_PRICE_DETAILS/ARTICLE_PRICE/@price_amount": "price",
        ...
    }
}

# Claude extrahiert mit Context
extracted = await intelligent_extractor.extract_to_standard_schema(
    file_content=xml_content,
    deployment_context=deployment_context,
    classification="products",
    filename="eaton_products.xml"
)

# Returns:
{
    "products": [
        {"gtin": "...", "sku": "123456", "name": "...", "price": 45.99},
        ...
    ],
    "data_quality": {
        "completeness": 0.98,
        "issues": ["12 products missing price"]
    }
}
```

**Claude Prompt** (Beispiel):
```
You are processing data for: EATON
Industry: Electrical Components

TASK: Extract structured product data from BMEcat XML.

TRANSFORMATION RULES:
- MANUFACTURER_AID → sku
- DESCRIPTION_SHORT → name
- ARTICLE_PRICE → price
- ETIM_CLASS → etim_classification

SOURCE DATA:
<ARTICLE>
  <MANUFACTURER_AID>EC-4567</MANUFACTURER_AID>
  <DESCRIPTION_SHORT>Contactor 3-pole</DESCRIPTION_SHORT>
  <ARTICLE_PRICE>89.50</ARTICLE_PRICE>
</ARTICLE>

Extract to JSON:
{
  "products": [
    {"sku": "EC-4567", "name": "Contactor 3-pole", "price": 89.50}
  ]
}
```

### 5. Entity Extractor
**File**: `ingestion/processor/entity_extractor.py`

**Extrahiert für Graph**:
- Companies (Named Entity Recognition)
- Products (aus strukturierten Daten)
- People (Ansprechpartner)
- Locations (Standorte, Lieferadressen)

**Beispiel**:
```
Text: "EATON liefert Schaltanlagen an Siemens in München"
  ↓
Entities:
  - Company: "EATON" (Supplier)
  - Company: "Siemens" (Customer)
  - Product: "Schaltanlagen"
  - Location: "München"
  ↓
Relationships:
  - (EATON)-[SUPPLIES]->(Siemens)
  - (Siemens)-[LOCATED_IN]->(München)
```

### 6. Ingestion Orchestrator (Koordiniert alles)
**File**: `ingestion/orchestrator.py`

**Kompletter Pipeline**:
```python
orchestrator = IngestionOrchestrator(
    lakehouse_path=Path("/data/lakehouse"),
    claude_api_key="sk-ant-...",
    embedding_model="multilingual-e5-large"
)

result = await orchestrator.ingest(
    folder_configs=[
        FolderConfig(
            path=Path("/uploads/eaton"),
            mcp_assignment="products",  # Optional hint
            recursive=True
        )
    ],
    customer_id="eaton"
)

# Pipeline läuft:
# 1. Crawl (FileCrawler) → Findet alle Dateien
# 2. Extract (mit auto-generierten Handlers)
# 3. Classify (Rule + Claude)
# 4. Analyze Schema (Claude)
# 5. Intelligent Extract (Claude mit Context)
# 6. Chunk & Embed (Embeddings-Service)
# 7. Extract Entities (spaCy + Claude)
# 8. Load to Lakehouse (Delta + Lance + Neo4j)

# Returns:
{
    "total_files": 669,
    "total_documents": 31807,
    "total_embeddings": 31807,
    "errors": [],
    "stats_by_mcp": {
        "products": 669,
        "tax": 0,
        "legal": 0
    }
}
```

---

## 🎯 Wie es im Admin Portal funktioniert

### Aktueller Flow (bereits implementiert!)

```
Admin uploaded Dateien via UI
  ↓
POST /api/upload/files?customer_id=eaton2&selected_mcps=ctax,law,etim
  ↓
Backend (api/routes/upload.py):
  1. Files → MinIO (bucket: customer-eaton2/)
  2. First upload detection → Trigger Deployment
  3. Background Task startet:
  ↓
IngestionOrchestrator.ingest()
  ├─ Stage 1: Claude generiert Handler (falls nötig)
  ├─ Stage 2: Klassifiziert Dokumente (Claude + Rules)
  ├─ Stage 3: Analysiert Schema (Claude)
  ├─ Stage 4: Extrahiert intelligent (Claude mit DEPLOYMENT.md)
  ├─ Stage 5: Extrahiert Entities (spaCy + Claude)
  ├─ Stage 6: Quality Check (Claude)
  ├─ Stage 7: Embeddings generieren (Cradle GPU)
  └─ Stage 8: Load zu Lakehouse (Delta + Lance + Neo4j)
  ↓
console_builder.py builds Docker image
  ↓
eaton2-intelligence:1.0 fertig!
  ↓
Admin kann downloaden
```

---

## 🤖 Claude Prompts (Beispiele)

### Classification Prompt
```
Analyze this document and classify into ONE category:

Categories:
- tax: Tax documents, DATEV, Jahresabschluss
- legal: Contracts, invoices, compliance
- products: Catalogs, ETIM, specifications
- hr: Employee records, payroll
- general: Everything else

Filename: liefervertrag_2024.pdf
Content:
"""
Liefervereinbarung zwischen EATON und Kunde X
Artikel: Schaltgeräte Typ XY...
"""

Output ONLY the category: legal
```

### Extraction Prompt
```
You are processing data for: EATON
Industry: Electrical Components

Extract product data from this BMEcat XML:
<ARTICLE>
  <MANUFACTURER_AID>EC-100</MANUFACTURER_AID>
  <DESCRIPTION_SHORT>Contactor</DESCRIPTION_SHORT>
</ARTICLE>

Map to schema:
{
  "sku": "EC-100",
  "name": "Contactor",
  ...
}
```

### Due Diligence Prompt
```
Review this extracted product data for quality:

Data: 669 products from EATON catalog

Check:
1. Completeness: Are all required fields present?
2. Consistency: Are prices/dimensions plausible?
3. Anomalies: Any outliers or suspicious values?
4. Duplicates: Same product multiple times?

Return JSON:
{
  "completeness_score": 0.95,
  "missing_fields": [...],
  "anomalies": [...],
  "recommendation": "..."
}
```

---

## 📊 Was macht das System intelligent?

### 1. **Adaptive** (lernt neue Formate)
- Erster Upload: .DAT unbekannt → Claude generiert Handler
- Zweiter Upload: .DAT bekannt → nutzt generierten Handler
- **Kein manuelles Coding mehr!**

### 2. **Context-Aware** (versteht Kunde)
- Liest DEPLOYMENT.md (Company, Industry, Rules)
- Wendet Customer-spezifische Transformationen an
- Versteht Branchen-Terminologie

### 3. **Multi-Strategy** (optimal & kosteneffizient)
- Rule-Based first (schnell, kostenlos)
- Claude nur wenn nötig (genau, kostet Tokens)
- Fallbacks auf allen Ebenen

### 4. **Quality-First** (Due Diligence eingebaut)
- Automatische Validierung
- Anomalie-Erkennung
- Reports für Admin

### 5. **Multi-Modal Storage** (optimal für jeden Datentyp)
- Strukturiert → Delta Lake (SQL)
- Entities → Neo4j (Graph)
- Text → LanceDB (Vektor-Suche)

---

## ✅ Aktueller Stand

**Wo läuft das?**:
- ✅ **Lightnet**: 104,699 Produkte, intelligent klassifiziert & extrahiert
- ✅ **EATON**: 669 Produkte, Claude-generierte .DAT Handler
- ✅ **Partner Portal**: Nutzt diesen Flow für Customer Onboarding
- ✅ **Admin Portal**: Nutzt diesen Flow (via upload endpoint)

**APIs**:
- `POST /api/upload/files` - Trigger kompletten Flow
- `POST /api/upload-async/start` - Async mit Progress-Polling
- `GET /api/upload/status/{job_id}` - Progress abfragen

---

## 🚀 Für neuen Kunden nutzen

**Im Admin Portal** (aktuell implementiert):
```
1. Upload Files via Drag & Drop
2. System macht automatisch:
   ✓ Handler Generation (falls nötig)
   ✓ Classification (Claude + Rules)
   ✓ Schema Analysis (Claude)
   ✓ Intelligent Extraction (mit Context)
   ✓ Entity Extraction (Graph)
   ✓ Due Diligence (Quality Check)
   ✓ Embeddings (GPU)
   ✓ Load to Lakehouse
3. Fertig!
```

**Kein manuelles Mapping, keine Config-Files, keine Schemas definieren - Claude macht alles automatisch!** 🤖✨

---

**Das ist der sophistizierte Teil den du gesucht hast!** 🎉
