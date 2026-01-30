"""
Lakehouse Service - Simple HTTP API for customer lakehouse data

Serves Delta Lake tables and LanceDB vectors over HTTP.
Mounts customer-specific lakehouse at /data/lakehouse/
"""

import logging
from pathlib import Path
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import pyarrow.parquet as pq
import pandas as pd

logger = logging.getLogger(__name__)


# Startup: Load lakehouse location
lakehouse_path = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global lakehouse_path
    lakehouse_path = Path("/data/lakehouse")

    logger.info(f"Lakehouse service starting")
    logger.info(f"  Path: {lakehouse_path}")
    logger.info(f"  Exists: {lakehouse_path.exists()}")

    if lakehouse_path.exists():
        delta_path = lakehouse_path / "delta"
        lance_path = lakehouse_path / "lance"

        if delta_path.exists():
            tables = list(delta_path.iterdir())
            logger.info(f"  Delta tables: {len(tables)}")

        if lance_path.exists():
            datasets = list(lance_path.iterdir())
            logger.info(f"  Lance datasets: {len(datasets)}")

    yield

    logger.info("Lakehouse service shutting down")


app = FastAPI(title="0711 Lakehouse Service", lifespan=lifespan)


class HealthResponse(BaseModel):
    status: str
    lakehouse_path: str
    exists: bool
    delta_tables: List[str]
    lance_datasets: List[str]


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    delta_tables = []
    lance_datasets = []

    if lakehouse_path and lakehouse_path.exists():
        delta_path = lakehouse_path / "delta"
        lance_path = lakehouse_path / "lance"

        if delta_path.exists():
            delta_tables = [t.name for t in delta_path.iterdir() if t.is_dir()]

        if lance_path.exists():
            lance_datasets = [d.name for d in lance_path.iterdir() if d.is_dir()]

    return HealthResponse(
        status="healthy",
        lakehouse_path=str(lakehouse_path),
        exists=lakehouse_path.exists() if lakehouse_path else False,
        delta_tables=delta_tables,
        lance_datasets=lance_datasets
    )


@app.get("/delta/tables")
async def list_delta_tables():
    """List available Delta Lake tables"""
    if not lakehouse_path or not lakehouse_path.exists():
        raise HTTPException(status_code=404, detail="Lakehouse not found")

    delta_path = lakehouse_path / "delta"
    if not delta_path.exists():
        return {"tables": []}

    tables = [
        {
            "name": table.name,
            "path": str(table),
            "files": len(list(table.glob("*.parquet")))
        }
        for table in delta_path.iterdir()
        if table.is_dir()
    ]

    return {"tables": tables}


@app.get("/delta/query/syndication_products")
async def query_syndication_products_specific(limit: int = Query(default=200, le=50000)):
    """
    Syndication products endpoint - auto-maps to available product table.

    MUST be defined BEFORE generic /delta/query/{table_name} for FastAPI routing!

    Tries: syndication_products → products → products_documents
    """
    if not lakehouse_path or not lakehouse_path.exists():
        raise HTTPException(status_code=404, detail="Lakehouse not found")

    delta_path = lakehouse_path / "delta"
    table_candidates = ["syndication_products", "products", "products_documents"]

    for table_name in table_candidates:
        table_path = delta_path / table_name
        if table_path.exists():
            parquet_files = list(table_path.glob("*.parquet"))
            if parquet_files:
                logger.info(f"Using {table_name} for syndication_products query (limit={limit})")
                table = pq.read_table(parquet_files[0])
                df = table.to_pandas()
                total_count = len(df)
                df = df.head(limit)  # Apply limit AFTER getting total count

                return {
                    "table": "syndication_products",
                    "rows": df.to_dict(orient="records"),
                    "count": len(df),
                    "total": total_count,
                    "source_table": table_name
                }

    # No data found
    return {"rows": [], "count": 0, "source_table": None}


@app.get("/delta/query/{table_name}")
async def query_delta_table(
    table_name: str,
    limit: int = Query(default=10, le=1000)
):
    """
    Query a Delta Lake table.

    Args:
        table_name: Name of table to query
        limit: Maximum rows to return

    Returns:
        Table data as JSON
    """
    if not lakehouse_path or not lakehouse_path.exists():
        raise HTTPException(status_code=404, detail="Lakehouse not found")

    table_path = lakehouse_path / "delta" / table_name
    if not table_path.exists():
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")

    # Try Delta Lake first (reads ALL parquet files), fallback to single parquet
    try:
        from deltalake import DeltaTable
        dt = DeltaTable(str(table_path))
        df = dt.to_pandas()
        total = len(df)
        df = df.head(limit)
        logger.info(f"Read Delta table {table_name}: {total} rows total, returning {len(df)}")
    except:
        # Fallback: Read parquet files directly
        parquet_files = list(table_path.glob("*.parquet"))
        if not parquet_files:
            return {"rows": [], "count": 0}

        table = pq.read_table(parquet_files[0])
        df = table.to_pandas()
        total = len(df)
        df = df.head(limit)
        logger.warning(f"Fallback to Parquet for {table_name}: {total} rows")

    return {
        "table": table_name,
        "rows": df.to_dict(orient="records"),
        "count": len(df)
    }


@app.get("/lance/datasets")
async def list_lance_datasets():
    """List available LanceDB datasets"""
    if not lakehouse_path or not lakehouse_path.exists():
        raise HTTPException(status_code=404, detail="Lakehouse not found")

    lance_path = lakehouse_path / "lance"
    if not lance_path.exists():
        return {"datasets": []}

    datasets = [
        {
            "name": dataset.name,
            "path": str(dataset),
        }
        for dataset in lance_path.iterdir()
        if dataset.is_dir() and dataset.suffix == ".lance"
    ]

    return {"datasets": datasets}


@app.get("/products")
async def list_products(limit: int = Query(default=100, le=50000)):
    """
    Smart products endpoint - auto-detects product table.

    Tries in order:
    1. products (structured catalog)
    2. products_documents (document-based)
    3. general_documents filtered by mcp=products
    """
    if not lakehouse_path or not lakehouse_path.exists():
        raise HTTPException(status_code=404, detail="Lakehouse not found")

    delta_path = lakehouse_path / "delta"

    # Try different table names (syndication_products first for Lightnet!)
    table_candidates = ["syndication_products", "products", "products_documents", "general_documents"]

    for table_name in table_candidates:
        table_path = delta_path / table_name
        if table_path.exists():
            parquet_files = list(table_path.glob("*.parquet"))
            if parquet_files:
                logger.info(f"Using {table_name} table for /products endpoint")

                # Try Delta Lake first, fallback to Parquet
                try:
                    from deltalake import DeltaTable
                    dt = DeltaTable(str(table_path))
                    df = dt.to_pandas()
                    total = len(df)
                    df = df.head(limit)
                    logger.info(f"Using Delta table {table_name} ({total} rows)")
                except:
                    # Fallback to Parquet
                    table = pq.read_table(parquet_files[0])
                    df = table.to_pandas()
                    total = len(df)
                    df = df.head(limit)
                    logger.info(f"Using Parquet {table_name} ({total} rows)")

                # Convert to product format
                products = df.to_dict(orient="records")

                return {
                    "products": products,
                    "total": total,
                    "source_table": table_name
                }

    # No product data found
    return {"products": [], "total": 0, "source_table": None}


@app.get("/stats")
async def get_stats():
    """Get lakehouse statistics"""
    if not lakehouse_path or not lakehouse_path.exists():
        raise HTTPException(status_code=404, detail="Lakehouse not found")

    stats = {
        "lakehouse_path": str(lakehouse_path),
        "delta_tables": 0,
        "lance_datasets": 0,
        "total_size_mb": 0
    }

    # Count Delta tables
    delta_path = lakehouse_path / "delta"
    if delta_path.exists():
        stats["delta_tables"] = len([t for t in delta_path.iterdir() if t.is_dir()])

    # Count Lance datasets
    lance_path = lakehouse_path / "lance"
    if lance_path.exists():
        stats["lance_datasets"] = len([d for d in lance_path.iterdir() if d.is_dir()])

    # Calculate total size
    total_size = sum(
        f.stat().st_size
        for f in lakehouse_path.rglob("*")
        if f.is_file()
    )
    stats["total_size_mb"] = round(total_size / (1024 * 1024), 2)

    return stats


class VectorSearchRequest(BaseModel):
    query: str
    limit: int = 5
    mcp_filter: Optional[str] = None


@app.post("/lance/search")
async def vector_search(request: VectorSearchRequest):
    """
    Semantic search using LanceDB vector embeddings.

    Converts query text to vector via embeddings service,
    then searches all embeddings in lakehouse.
    """
    if not lakehouse_path or not lakehouse_path.exists():
        raise HTTPException(status_code=404, detail="Lakehouse not found")

    lance_path = lakehouse_path / "lance"
    if not lance_path.exists():
        raise HTTPException(status_code=404, detail="Lance database not found")

    try:
        import lancedb
        import httpx
        import os

        # Connect to Lance database
        db = lancedb.connect(str(lance_path))
        table = db.open_table("embeddings")

        # Get embedding service URL from environment
        # For Docker: use service name on internal network
        # For host: use localhost with external port
        customer_id = os.getenv("CUSTOMER_ID", "unknown")
        embedding_url = os.getenv(
            "EMBEDDING_SERVICE_URL",
            f"http://{customer_id}-embeddings:8001"  # Internal Docker network
        )

        # Convert query to vector via embeddings service
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                embed_response = await client.post(
                    f"{embedding_url}/v1/embeddings",
                    json={"input": [request.query], "model": "multilingual-e5-large"}
                )

                if embed_response.status_code != 200:
                    # Fallback to text search if embeddings service unavailable
                    logger.warning(f"Embeddings service unavailable, using text search")
                    results_df = table.to_pandas()
                    query_lower = request.query.lower()
                    mask = results_df['text'].str.lower().str.contains(query_lower, na=False)
                    filtered = results_df[mask].head(request.limit)

                    if request.mcp_filter:
                        filtered = filtered[filtered['mcp'] == request.mcp_filter]

                    return {
                        "query": request.query,
                        "results": filtered[['filename', 'text', 'mcp', 'chunk_index']].to_dict(orient="records"),
                        "count": len(filtered),
                        "search_type": "text",
                        "note": "Embeddings service unavailable, used text search"
                    }

                embed_data = embed_response.json()
                # OpenAI format: {"data": [{"embedding": [...]}]}
                query_vector = embed_data['data'][0]['embedding']

        except Exception as e:
            logger.error(f"Embedding service error: {e}")
            raise HTTPException(status_code=503, detail=f"Embeddings service unavailable: {str(e)}")

        # Perform vector search
        search_query = table.search(query_vector).limit(request.limit * 2)

        # Apply MCP filter if specified
        if request.mcp_filter:
            search_query = search_query.where(f"mcp = '{request.mcp_filter}'")

        results = search_query.to_list()

        # Format results (remove vector field, it's huge)
        formatted_results = []
        for r in results[:request.limit]:
            formatted_results.append({
                "filename": r.get("filename"),
                "text": r.get("text"),
                "mcp": r.get("mcp"),
                "chunk_index": r.get("chunk_index"),
                "score": r.get("_distance", 0.0)  # LanceDB returns _distance
            })

        return {
            "query": request.query,
            "results": formatted_results,
            "count": len(formatted_results),
            "total_searched": table.count_rows(),
            "search_type": "semantic",
            "embedding_service": embedding_url
        }

    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/products")
async def list_products(
    limit: int = Query(default=50, le=500),
    offset: int = Query(default=0, ge=0),
    search: str = Query(default=None)
):
    """
    List products from syndication_products or eaton_products table.

    Returns structured product records.
    """
    if not lakehouse_path or not lakehouse_path.exists():
        raise HTTPException(status_code=404, detail="Lakehouse not found")

    # Try syndication_products first, then eaton_products as fallback
    table_path = lakehouse_path / "delta" / "syndication_products"
    if not table_path.exists():
        table_path = lakehouse_path / "delta" / "eaton_products"

    if not table_path.exists():
        return {"products": [], "total": 0}

    try:
        from deltalake import DeltaTable
        dt = DeltaTable(str(table_path))
        df = dt.to_pandas()

        # Search filter if provided (work with whatever columns exist)
        if search:
            search_cols = []
            for col in ['product_name', 'sku', 'short_description', 'long_description', 'supplier_pid']:
                if col in df.columns:
                    search_cols.append(df[col].astype(str).str.contains(search, case=False, na=False))

            if search_cols:
                mask = search_cols[0]
                for s in search_cols[1:]:
                    mask = mask | s
                df = df[mask]

        total = len(df)
        df = df.iloc[offset:offset+limit]

        # Convert to records with NaN handling
        import math
        records = []
        for _, row in df.iterrows():
            record = {}
            for key, value in row.items():
                # Handle NaN, None, Inf
                if pd.isna(value) or value is None:
                    record[key] = None
                elif isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
                    record[key] = None
                else:
                    record[key] = value
            records.append(record)

        return {
            "products": records,
            "total": total,
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        logger.error(f"Failed to list products: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/products/categories")
async def get_product_categories():
    """
    Get 3-level product hierarchy for tree navigation.

    Level 1: Product Family (Caleo, Ringo Star, etc.)
    Level 2: Light Distribution (Direktstrahlend, Indirekt, etc.)
    Level 3: Color Temperature (3000K, 4000K, Tunable White, etc.)
    """
    if not lakehouse_path or not lakehouse_path.exists():
        raise HTTPException(status_code=404, detail="Lakehouse not found")

    try:
        from deltalake import DeltaTable
        from collections import defaultdict

        # Get products table
        products_path = lakehouse_path / "delta" / "syndication_products"
        if not products_path.exists():
            raise HTTPException(status_code=404, detail="Products table not found")

        dt = DeltaTable(str(products_path))
        df = dt.to_pandas()

        # Build 2-level hierarchy (Familie → Farbtemperatur)
        # SKIP light_distribution - die Spalte enthält falsche Daten (ISO-Zertifikate)
        hierarchy = defaultdict(lambda: defaultdict(int))

        # Extract ONLY known Lightnet product families
        def extract_family(product_name, short_desc):
            if not product_name and not short_desc:
                return 'Other'

            search_text = f"{product_name or ''} {short_desc or ''}".lower()

            # Known Lightnet families (in priority order)
            families = [
                'Caleo', 'Ringo Star', 'Cubic', 'Basic', 'Code Zero', 'Liquid Line',
                'Matric', 'Manto', 'Pal', 'Arc', 'Grid', 'Flek', 'Conus', 'Vision',
                'Beam Me Up', 'Lightpad', 'Code'
            ]

            for fam in families:
                if fam.lower() in search_text:
                    return fam

            # If no known family found, use "Other"
            return 'Other'

        # Categorize products and collect top 10 per family
        family_products = defaultdict(list)

        for _, row in df.iterrows():
            product_name = row.get('product_name', '') or ''
            short_desc = row.get('short_description', '') or ''
            family = extract_family(product_name, short_desc)
            temp = row.get('color_temperature', 'Unknown') or 'Unknown'

            # Bereinige Farbtemperatur (nur echte Temperaturen)
            if temp and any(x in temp for x in ['3000K', '4000K', '2700K', '6500K', 'Tunable', 'RGB']):
                hierarchy[family][temp] += 1
            else:
                hierarchy[family]['Other'] += 1

            # Collect top 10 products per family
            if len(family_products[family]) < 10:
                family_products[family].append({
                    "code": row.get('sku', ''),
                    "name": row.get('product_name', ''),
                    "price": row.get('price_eur', ''),
                    "description": row.get('short_description', '')
                })

        # Convert to 2-level nested structure (Familie → Farbtemperatur)
        categories = []
        for family, temps in sorted(hierarchy.items()):
            family_count = sum(temps.values())

            # Subcategories by color temperature
            subcats = [
                {
                    "name": temp,
                    "count": count,
                    "filters": {
                        "product_family": family,
                        "color_temperature": temp
                    }
                }
                for temp, count in sorted(temps.items(), key=lambda x: x[1], reverse=True)
            ]

            # Add top 10 products for this family
            categories.append({
                "id": family,  # Add ID for frontend
                "name": family,
                "count": family_count,
                "subcategories": subcats,
                "products": family_products[family],  # Top 10 products
                "filters": {
                    "product_family": family
                }
            })

        # Sort by count
        categories.sort(key=lambda x: x['count'], reverse=True)

        total_products = sum(c['count'] for c in categories)

        return {
            "categories": categories,
            "total_products": total_products,
            "total_families": len(categories)
        }

    except Exception as e:
        logger.error(f"Failed to generate categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/products/search/{sku}")
async def search_product_by_sku(sku: str):
    """
    Search for a product by SKU in syndication_products table.
    Returns single product or 404.
    """
    if not lakehouse_path or not lakehouse_path.exists():
        raise HTTPException(status_code=404, detail="Lakehouse not found")

    try:
        from deltalake import DeltaTable

        products_path = lakehouse_path / "delta" / "syndication_products"
        if not products_path.exists():
            raise HTTPException(status_code=404, detail="Products table not found")

        dt = DeltaTable(str(products_path))
        df = dt.to_pandas()

        # Find by SKU
        matches = df[df['sku'] == sku]

        if len(matches) == 0:
            raise HTTPException(status_code=404, detail=f"Product {sku} not found")

        product = matches.iloc[0].to_dict()

        # Clean NaN values
        import math
        cleaned = {}
        for key, value in product.items():
            if pd.isna(value) or value is None:
                cleaned[key] = None
            elif isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
                cleaned[key] = None
            else:
                cleaned[key] = value

        return {
            "product": cleaned,
            "sku": sku
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to search product {sku}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/products/{product_id}")
async def get_product_with_images(product_id: str):
    """
    Get product details with linked images.

    Returns:
    - Product info from eaton_products
    - All linked images from product_images
    - Vision API metadata for each image
    """
    if not lakehouse_path or not lakehouse_path.exists():
        raise HTTPException(status_code=404, detail="Lakehouse not found")

    try:
        from deltalake import DeltaTable

        # Get product
        products_path = lakehouse_path / "delta" / "eaton_products"
        if not products_path.exists():
            raise HTTPException(status_code=404, detail="Products table not found")

        dt = DeltaTable(str(products_path))
        df = dt.to_pandas()
        product = df[df['supplier_pid'] == product_id]

        if len(product) == 0:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")

        product_data = product.iloc[0].to_dict()

        # Get linked images
        images_path = lakehouse_path / "delta" / "product_images"
        images = []
        if images_path.exists():
            img_dt = DeltaTable(str(images_path))
            img_df = img_dt.to_pandas()
            product_images = img_df[img_df['product_id'] == product_id]
            images = product_images.to_dict(orient="records")

        return {
            "product": product_data,
            "images": images,
            "image_count": len(images)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get product: {e}")
        raise HTTPException(status_code=500, detail=str(e))
# ==============================================================================
# Graph Database Endpoints (Neo4j)
# ==============================================================================

# Lazy load graph store
_graph_store = None

def get_graph_store():
    """Get or create Neo4j graph store connection"""
    global _graph_store
    if _graph_store is None:
        try:
            import os
            from lakehouse.graph import Neo4jStore, GraphConfig

            config = GraphConfig(
                uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
                username=os.getenv("NEO4J_USER", "neo4j"),
                password=os.getenv("NEO4J_PASSWORD", "zeroseven2024")
            )

            customer_id = os.getenv("CUSTOMER_ID", "default")
            _graph_store = Neo4jStore(config=config, customer_id=customer_id)
            logger.info(f"✅ Neo4j graph store initialized for customer: {customer_id}")

        except Exception as e:
            logger.warning(f"Neo4j not available: {e}")
            _graph_store = None

    return _graph_store


@app.get("/graph/stats")
async def get_graph_stats():
    """Get graph database statistics"""
    graph = get_graph_store()
    if not graph:
        raise HTTPException(status_code=503, detail="Graph database not available")

    try:
        stats = graph.get_graph_stats()
        return {
            "status": "healthy",
            "customer_id": graph.customer_id,
            **stats
        }
    except Exception as e:
        logger.error(f"Failed to get graph stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/graph/entities")
async def list_entities(
    limit: int = Query(100, description="Max entities to return"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type (PERSON, ORG, PRODUCT, etc.)")
):
    """List all entities in the knowledge graph"""
    graph = get_graph_store()
    if not graph:
        raise HTTPException(status_code=503, detail="Graph database not available")

    try:
        entities = graph.get_all_entities(limit=limit)

        # Filter by type if specified
        if entity_type:
            entities = [e for e in entities if e["type"] == entity_type.upper()]

        return {
            "entities": entities,
            "count": len(entities),
            "customer_id": graph.customer_id
        }
    except Exception as e:
        logger.error(f"Failed to list entities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/graph/entities/{entity_id}/related")
async def get_related_entities(
    entity_id: str,
    max_hops: int = Query(2, description="Maximum relationship hops", ge=1, le=5)
):
    """Find entities related to given entity"""
    graph = get_graph_store()
    if not graph:
        raise HTTPException(status_code=503, detail="Graph database not available")

    try:
        related = graph.get_related_entities(entity_id, max_hops=max_hops)

        return {
            "entity_id": entity_id,
            "related": related,
            "count": len(related),
            "max_hops": max_hops
        }
    except Exception as e:
        logger.error(f"Failed to get related entities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/graph/query")
async def execute_cypher_query(query: str):
    """
    Execute custom Cypher query.

    WARNING: This endpoint should be protected/restricted in production!
    """
    graph = get_graph_store()
    if not graph:
        raise HTTPException(status_code=503, detail="Graph database not available")

    try:
        results = graph.query_cypher(query)

        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"Cypher query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
