# Claude Intelligent Data Router - Implementation Spec

**Created**: 2026-01-23
**Status**: Design Complete, Implementation In Progress
**Priority**: HIGH - Core differentiator

---

## 🎯 Vision

Transform generic file ingestion into **intelligent multi-modal data routing** where Claude:
1. Analyzes data structure and quality
2. Determines optimal storage strategy (SQL + Graph + Vector)
3. Extracts structured data intelligently
4. Preserves existing quality metadata
5. Generates dynamic prompts based on discovered schema

---

## 📊 Current vs. Target State

### **Current (Generic Ingestion)**
```
JSON file → Extract as text → Chunk → Embed → Save to products_documents
```

**Problems:**
- ❌ Loses structured data (GTIN, prices, ETIM codes)
- ❌ No SQL tables for querying
- ❌ No graph relationships
- ❌ Products/Syndicate pages can't display data

### **Target (Intelligent Routing)**
```
JSON file
  ↓
🧠 Claude analyzes structure
  ↓
Routes to optimal storage:
  ├─ SQL: products, specs, pricing (queryable)
  ├─ Graph: Product→Manufacturer→Parts (relationships)
  └─ Vector: Descriptions, highlights (searchable)
  ↓
✅ Data, Products, Syndicate pages all work
```

---

## 🏗️ Architecture

### **Phase 1: Schema Analysis** (New)

**Module**: `ingestion/analyzer/schema_analyzer.py` ✅ Created

**Input**: File content + classification
**Output**: `StorageStrategy` with:
- SQL table schemas (columns, types, relationships)
- Graph entity definitions (nodes, edges)
- Vector index specifications (which fields to embed)

**Claude Prompt**:
```
Analyze this {classification} file and design multi-modal storage.

Content: {json_sample}

Determine:
1. SQL Tables - Structured queryable data
2. Graph Entities - Relationships to model
3. Vector Indices - Text to make searchable

Output JSON with table schemas, graph model, vector fields.
```

---

### **Phase 2: Due Diligence** (Preserve Existing)

**Bosch JSON files already include:**
```json
"data_quality": {
  "completeness_percentage": 75,
  "data_sources": {
    "from_database": 25,
    "from_datasheet": 55,
    "estimated": 12
  },
  "confidence_levels": {
    "high_confidence": ["energy_ratings", "dimensions"],
    "medium_confidence": ["refrigerant_specs"],
    "needs_verification": ["compressor_type"]
  },
  "extraction_notes": [...]
}
```

**Action**: Extract and store in separate `data_quality` table

---

### **Phase 3: Intelligent Extraction** (New)

**Module**: `lakehouse/delta/intelligent_loader.py` (To Create)

**Process**:
```python
async def load_with_intelligence(file, schema_analysis):
    data = json.loads(file.read_text())

    # 1. Extract to SQL tables
    for table in schema_analysis.sql_tables:
        records = extract_json_path(data, table.json_path)
        await delta.create_table(table.name, table.columns, records)

    # 2. Build graph
    for entity in schema_analysis.graph_entities:
        nodes = extract_entities(data, entity)
        await neo4j.create_nodes(entity.type, nodes)

    # 3. Index vectors
    for index in schema_analysis.vector_indices:
        text = extract_fields(data, index.fields)
        embedding = await embedder.embed(text)
        await lance.add(embedding)

    # 4. Preserve data quality
    if "data_quality" in data:
        await delta.insert("data_quality_audit", data["data_quality"])
```

---

### **Phase 4: Dynamic Lakehouse API** (New)

**Module**: `lakehouse/server.py` (Update)

**Auto-generate endpoints from discovered tables**:
```python
# On startup, scan Delta tables
tables = delta.list_tables()  # ["products", "specs", "pricing", "spare_parts"]

# Generate endpoints dynamically
for table in tables:
    @app.get(f"/{table}")
    async def list_table(limit: int = 100):
        return delta.query(f"SELECT * FROM {table} LIMIT {limit}")
```

**Result**:
- `/products` → Returns structured product catalog
- `/specs` → Technical specifications
- `/spare_parts` → Replacement components
- `/manufacturers` → Company data

---

## 🚀 Implementation Phases

### **✅ DONE** (Today)
1. ✅ Multi-tenant isolation
2. ✅ Claude-first classification
3. ✅ Schema Analyzer module created
4. ✅ Data quality metadata discovered

### **Phase 1: Schema-Driven Loading** (Next)
1. Complete `schema_analyzer.py`
2. Create `intelligent_loader.py`
3. Update orchestrator to use schema analysis
4. Test with Bosch JSON

### **Phase 2: Multi-Modal Storage** (Week 2)
1. Implement graph builder
2. Create dynamic table generation
3. Add quality audit tables
4. Test Products/Syndicate pages

### **Phase 3: Dynamic API** (Week 3)
1. Auto-generate lakehouse endpoints
2. Schema-aware querying
3. GraphQL support
4. Full integration test

---

## 📝 Key Design Decisions

### **1. Claude Models**
- **Sonnet 4.5**: Schema analysis (complex, needs intelligence)
- **Haiku 3.5**: Classification (fast, cheap)
- **Sonnet 4.5**: Handler generation (code quality)

### **2. Data Quality Strategy**
- **Preserve existing**: Don't regenerate if already present
- **Add validation layer**: Claude verifies completeness
- **Track lineage**: Document all transformations

### **3. Storage Routing**
- **Products**: SQL (products) + Graph (relationships) + Vector (descriptions)
- **Tax docs**: Primarily Vector + metadata in SQL
- **Contracts**: Vector + entity extraction to Graph

---

## 🎯 Success Criteria

✅ **Data Page**: Shows all ingested documents
✅ **Products Page**: Displays structured product catalog
✅ **Syndicate Page**: Exports BMEcat/ETIM from SQL
✅ **Search**: Semantic search across all content
✅ **Quality**: Data completeness tracked and displayed
✅ **Graph**: "Find all A++ rated heat pumps from Bosch"

---

**Status**: Foundation complete, ready for intelligent loader implementation.
