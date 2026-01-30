# Lakehouse Standard Schemas

**Created**: 2026-01-23
**Purpose**: Define standard table schemas that ALL ingestion must create

---

## 🎯 Principle

**The lakehouse has ONE standard schema.**

All ingestion processes must transform source data into these tables, regardless of format.
The UI expects these tables and only these tables.

---

## 📊 Standard Tables

### **1. `general_documents`** (Required)
Every file ingested creates ONE row here.

**Schema:**
```sql
CREATE TABLE general_documents (
    id STRING PRIMARY KEY,              -- Unique document ID
    filename STRING NOT NULL,            -- Original filename
    filepath STRING,                     -- Original path
    mcp STRING,                          -- Assigned MCP (tax, legal, products, etc.)
    category STRING,                     -- Sub-category
    text TEXT,                           -- Full extracted text content
    chunk_count INTEGER,                 -- Number of chunks created
    size_bytes INTEGER,                  -- File size
    mime_type STRING,                    -- MIME type
    ingested_at TIMESTAMP,               -- When ingested
    modified_at TIMESTAMP,               -- Source file modification time
    metadata JSON                        -- Flexible metadata
);
```

**Purpose**: Central registry of all documents

---

### **2. `general_chunks`** (Required)
Text chunks for vector search.

**Schema:**
```sql
CREATE TABLE general_chunks (
    id STRING PRIMARY KEY,
    document_id STRING,                  -- FK to general_documents
    chunk_index INTEGER,                 -- Position in document
    text TEXT NOT NULL,                  -- Chunk text
    embedding_id STRING,                 -- Link to Lance vector
    tokens INTEGER,                      -- Token count
    mcp STRING,                          -- Inherited from document
    created_at TIMESTAMP
);
```

**Purpose**: Searchable text chunks

---

### **3. `products`** (Optional - for product data)
Structured product catalog.

**Schema:**
```sql
CREATE TABLE products (
    gtin STRING PRIMARY KEY,             -- Global Trade Item Number
    supplier_pid STRING,                 -- Supplier product ID
    manufacturer_pid STRING,             -- Manufacturer product ID
    brand STRING,                        -- Brand name
    product_name STRING,                 -- Product name
    short_description TEXT,              -- Short description
    long_description TEXT,               -- Long description
    price DECIMAL,                       -- List price
    currency STRING,                     -- Currency code
    etim_class STRING,                   -- ETIM classification
    eclass_id STRING,                    -- ECLASS classification
    manufacturer_name STRING,            -- Manufacturer
    product_type STRING,                 -- Type/category
    status STRING,                       -- Active/discontinued
    source_document_id STRING,           -- FK to general_documents
    ingested_at TIMESTAMP,
    metadata JSON                        -- Full product data as JSON
);
```

**Purpose**: Queryable product catalog for Products page

---

### **4. `syndication_products`** (Optional - for exports)
Products formatted for syndication/export.

**Schema:**
```sql
CREATE TABLE syndication_products (
    id STRING PRIMARY KEY,
    gtin STRING,
    supplier_pid STRING,
    product_name STRING,
    description TEXT,
    price DECIMAL,
    currency STRING,
    etim_class STRING,
    eclass_id STRING,
    manufacturer STRING,
    brand STRING,
    images JSON,                         -- Array of image URLs
    cad_files JSON,                      -- Array of CAD file URLs
    technical_specs JSON,                -- Structured specs
    compliance_data JSON,                -- Certifications, regulations
    bmecat_ready BOOLEAN,                -- Ready for BMEcat export
    etim_compliant BOOLEAN,              -- ETIM format compliant
    export_formats JSON,                 -- Supported formats
    last_updated TIMESTAMP
);
```

**Purpose**: Syndication/export for Syndicate page

---

### **5. `data_quality_audit`** (Optional)
Track data quality and completeness.

**Schema:**
```sql
CREATE TABLE data_quality_audit (
    document_id STRING PRIMARY KEY,      -- FK to general_documents
    completeness_percentage INTEGER,     -- 0-100%
    data_sources JSON,                   -- Source breakdown
    confidence_levels JSON,              -- high/medium/low fields
    extraction_notes JSON,               -- Processing notes
    validation_errors JSON,              -- Any issues found
    verified BOOLEAN,                    -- Human verified
    verified_by STRING,                  -- User who verified
    verified_at TIMESTAMP
);
```

**Purpose**: Data quality tracking

---

## 🔄 Ingestion Standard Process

### **Step 1: Always Create Base Tables**
```python
# Every ingestion MUST create:
1. general_documents (1 row per file)
2. general_chunks (N rows per file)
3. Lance embeddings (vectors for all chunks)
```

### **Step 2: Conditionally Create Domain Tables**
```python
if classification == "products":
    # Parse JSON and create:
    - products table (structured catalog)
    - syndication_products (export-ready)

elif classification in ["tax", "legal"]:
    # Just use general_documents + chunks
    pass
```

### **Step 3: Preserve Quality Metadata**
```python
if "data_quality" in source_json:
    # Extract and store
    data_quality_audit.insert(source_json["data_quality"])
```

---

## 🎯 Benefits

✅ **Predictable**: UI knows exactly what tables exist
✅ **Simple**: No dynamic endpoint generation needed
✅ **Extensible**: Add new standard tables as needed
✅ **Compatible**: Works with any source data format
✅ **Testable**: Clear contracts between ingestion and UI

---

## 📋 Implementation Checklist

- [ ] Update Delta loader to always create standard tables
- [ ] Update orchestrator to use standard schemas
- [ ] Products page queries `products` table
- [ ] Syndicate page queries `syndication_products` table
- [ ] Data page queries `general_documents` table
- [ ] All tables work across all tenants

---

**Next**: Update ingestion to follow these standards
