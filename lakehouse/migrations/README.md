# Bosch Data Migration Scripts

Complete migration pipeline from Bosch PostgreSQL to 0711-OS lakehouse.

## 📊 Overview

**Source**: Bosch standalone PostgreSQL (port 5434)
**Target**: 0711-OS Lakehouse (Delta Lake + LanceDB + Neo4j)
**Data**: 23,138 products, 17,716 embeddings, 5,000 graph edges

## 🚀 Quick Start

### Step 1: Export from Bosch PostgreSQL

```bash
cd /home/christoph.bertsch/0711/0711-OS

# Export all data
python3 -m lakehouse.migrations.bosch_export \
  --host localhost \
  --port 5434 \
  --database bosch_products \
  --user bosch_user \
  --password bosch_secure_2024 \
  --what all

# Export specific components
python3 -m lakehouse.migrations.bosch_export --what products
python3 -m lakehouse.migrations.bosch_export --what embeddings
python3 -m lakehouse.migrations.bosch_export --what relationships
python3 -m lakehouse.migrations.bosch_export --what eclass-etim
```

**Output**: `/lakehouse/clients/bosch/export/`
- `products_chunk_*.parquet`
- `features_chunk_*.parquet`
- `embeddings.npz`
- `relationships.parquet`
- `*_classifications.parquet`
- `export_summary.json`

**Time**: ~5-10 minutes for full export

---

### Step 2: Import to 0711-OS Lakehouse

```bash
# Import all data
python3 -m lakehouse.migrations.bosch_import \
  --export-dir lakehouse/clients/bosch/export \
  --neo4j-uri bolt://localhost:7687 \
  --neo4j-user neo4j \
  --neo4j-password your_password \
  --what all

# Import specific components
python3 -m lakehouse.migrations.bosch_import --what products
python3 -m lakehouse.migrations.bosch_import --what embeddings
python3 -m lakehouse.migrations.bosch_import --what graph
python3 -m lakehouse.migrations.bosch_import --what classifications
```

**Output**:
- Delta Lake: `/lakehouse/clients/bosch/delta/`
  - `products/`
  - `features/`
  - `etim_classifications/`
  - `eclass_classifications/`
- LanceDB: `/lakehouse/clients/bosch/vector/`
  - `product_embeddings/` (with IVF-PQ index)
- Neo4j: `bolt://localhost:7687`
  - Nodes: `(:Product {client: 'bosch'})`
  - Edges: `[:RELATED {type: '...', strength: ...}]`

**Time**: ~10-15 minutes for full import

---

## 📋 Prerequisites

### Python Dependencies

```bash
pip install psycopg2-binary pandas numpy pyarrow delta-spark pyspark lancedb neo4j
```

### Database Access

**Bosch PostgreSQL** (source):
- Host: localhost
- Port: 5434
- Database: bosch_products
- User: bosch_user
- Password: bosch_secure_2024

**Neo4j** (target):
- URI: bolt://localhost:7687
- User: neo4j
- Password: (set your password)

---

## 🔍 Data Validation

### After Export

```bash
# Check export summary
cat lakehouse/clients/bosch/export/export_summary.json

# Expected:
# {
#   "data_exported": {
#     "products": 23138,
#     "embeddings": 17716,
#     "relationships": 5000,
#     ...
#   }
# }
```

### After Import

```bash
# Check import summary
cat lakehouse/clients/bosch/delta/import_summary.json

# Query Delta Lake
python3 -c "
from pyspark.sql import SparkSession
spark = SparkSession.builder.appName('test').getOrCreate()
df = spark.read.format('delta').load('lakehouse/clients/bosch/delta/products')
print(f'Products: {df.count()}')
"

# Query LanceDB
python3 -c "
import lancedb
db = lancedb.connect('lakehouse/clients/bosch/vector')
table = db.open_table('product_embeddings')
print(f'Embeddings: {table.count_rows()}')
"

# Query Neo4j
cypher-shell -u neo4j -p your_password \
  "MATCH (p:Product {client: 'bosch'}) RETURN count(p)"
```

---

## 🐛 Troubleshooting

### Export Issues

**Error: Connection refused (PostgreSQL)**
```bash
# Check if Bosch PostgreSQL is running
psql -h localhost -p 5434 -U bosch_user -d bosch_products -c "SELECT COUNT(*) FROM products"

# If not running, start it
cd /path/to/Bosch/0711
docker-compose up -d bosch_postgres
```

**Error: Out of memory**
```bash
# Export in smaller chunks (modify chunk_size in script)
# Default is 5000 for products, 10000 for features
```

### Import Issues

**Error: Neo4j connection failed**
```bash
# Check Neo4j is running
docker ps | grep neo4j

# Start Neo4j if needed
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your_password \
  neo4j:latest
```

**Error: Spark/Delta issues**
```bash
# Increase Spark memory
export SPARK_DRIVER_MEMORY=4g
export SPARK_EXECUTOR_MEMORY=4g

# Or edit the script's _init_spark() method
```

---

## 📈 Performance Tips

### For Large Datasets

1. **Export**: Use parallel exports
```bash
# Export in parallel (different terminals)
python3 -m lakehouse.migrations.bosch_export --what products &
python3 -m lakehouse.migrations.bosch_export --what embeddings &
python3 -m lakehouse.migrations.bosch_export --what relationships &
wait
```

2. **Import**: Increase batch sizes
```python
# In bosch_import.py, increase:
batch_size = 5000  # for Neo4j import
```

3. **Neo4j**: Create indexes first
```cypher
CREATE INDEX product_client IF NOT EXISTS FOR (p:Product) ON (p.client);
CREATE INDEX product_id IF NOT EXISTS FOR (p:Product) ON (p.id);
```

---

## 🧹 Cleanup

### Remove Exported Data (after successful import)

```bash
# Keep summary, remove data files
cd lakehouse/clients/bosch/export
rm -f products_chunk_*.parquet
rm -f features_chunk_*.parquet
rm -f embeddings.npz
rm -f relationships.parquet
# Keep: export_summary.json
```

### Re-import (clean slate)

```bash
# Clean Delta tables
rm -rf lakehouse/clients/bosch/delta/products
rm -rf lakehouse/clients/bosch/delta/features

# Clean LanceDB
rm -rf lakehouse/clients/bosch/vector/product_embeddings

# Clean Neo4j (via Cypher)
cypher-shell -u neo4j -p password \
  "MATCH (p:Product {client: 'bosch'}) DETACH DELETE p"

# Re-run import
python3 -m lakehouse.migrations.bosch_import --what all
```

---

## 📊 Migration Checklist

- [ ] Bosch PostgreSQL accessible (port 5434)
- [ ] Neo4j running (port 7687)
- [ ] Python dependencies installed
- [ ] Export directory created
- [ ] Run export script
- [ ] Verify export summary
- [ ] Run import script
- [ ] Verify import summary
- [ ] Test queries (Delta, Lance, Neo4j)
- [ ] Update Bosch MCP to use lakehouse
- [ ] Test via 0711-OS console

---

## 📞 Support

**Scripts**: `lakehouse/migrations/`
- `bosch_export.py` - Export from PostgreSQL
- `bosch_import.py` - Import to lakehouse
- `README.md` - This file

**Documentation**:
- Main plan: `BOSCH_COMPLETE_INTEGRATION.md`
- Client guide: `clients/bosch/README.md`

**Issues**: Check logs in console output
