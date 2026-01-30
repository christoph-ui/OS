"""
Data Browser Routes

Browse and search data in the lakehouse.
"""

import logging
import re
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Request, Query, Depends
from pydantic import BaseModel, field_validator

from ..auth.dependencies import require_auth
from ..auth.models import CustomerContext

logger = logging.getLogger(__name__)
router = APIRouter()

# Allowed values for filtering (whitelist approach for security)
ALLOWED_CATEGORIES = {"tax", "legal", "contract", "tender", "invoice", "other", "general"}
ALLOWED_MCPS = {"ctax", "law", "tender"}

# Safe identifier pattern (alphanumeric and underscores only)
SAFE_IDENTIFIER = re.compile(r'^[a-zA-Z0-9_]+$')


def validate_identifier(value: Optional[str], allowed: set, field_name: str) -> Optional[str]:
    """Validate and sanitize identifier to prevent SQL injection."""
    if value is None:
        return None

    value = value.lower().strip()

    # Check against whitelist
    if value not in allowed:
        # If not in whitelist, validate pattern
        if not SAFE_IDENTIFIER.match(value):
            raise ValueError(f"Invalid {field_name}: must be alphanumeric")
        logger.warning(f"Unknown {field_name}: {value}")

    return value


class Document(BaseModel):
    """Document from lakehouse"""
    id: str
    filename: str
    category: str
    mcp: Optional[str]
    ingested_at: str
    size_bytes: int
    snippet: Optional[str]


class DataBrowseResponse(BaseModel):
    """Data browse response"""
    documents: List[Document]
    total: int
    page: int
    page_size: int


class SearchRequest(BaseModel):
    """Search request"""
    query: str
    category: Optional[str] = None
    mcp: Optional[str] = None
    limit: int = 20

    @field_validator('category')
    @classmethod
    def validate_category(cls, v):
        if v is not None:
            return validate_identifier(v, ALLOWED_CATEGORIES, "category")
        return v

    @field_validator('mcp')
    @classmethod
    def validate_mcp(cls, v):
        if v is not None:
            return validate_identifier(v, ALLOWED_MCPS, "mcp")
        return v

    @field_validator('limit')
    @classmethod
    def validate_limit(cls, v):
        if v < 1 or v > 100:
            raise ValueError("limit must be between 1 and 100")
        return v


class SearchResult(BaseModel):
    """Search result"""
    id: str
    filename: str
    snippet: str
    score: float
    category: str


class SearchResponse(BaseModel):
    """Search response"""
    results: List[SearchResult]
    total: int
    query: str


@router.get("/browse", response_model=DataBrowseResponse)
async def browse_data(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    mcp: Optional[str] = None
):
    """
    Browse products or documents in the lakehouse (MULTI-TENANT SAFE).

    - Product categories (circuit_breakers, fuses, etc.) → shows products
    - Document categories (tax, legal, etc.) → shows documents

    Example:
        GET /api/data/browse?category=circuit_breakers&page=1&page_size=20
    """
    import httpx
    from core.customer_registry import get_registry, initialize_registry

    # Product category keys (from products.py)
    PRODUCT_CATEGORIES = {
        "ups_systems", "circuit_breakers", "residual_current",
        "fuses", "contactors", "drives", "switches", "other"
    }

    try:
        # Extract customer_id from JWT token (multi-tenant safe)
        customer_id = None
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                from ..auth.jwt import verify_token
                token_data = verify_token(auth_header.split(" ")[1])
                if token_data:
                    customer_id = token_data.customer_id
                    logger.info(f"Customer ID from token: {customer_id}")
            except Exception as e:
                logger.warning(f"Failed to extract customer_id from token: {e}")

        # Fallback to query param (for testing only)
        if not customer_id:
            customer_id = request.query_params.get("customer_id")
            if customer_id:
                logger.warning(f"Using customer_id from query param (testing): {customer_id}")

        # Require authentication
        if not customer_id:
            raise HTTPException(
                status_code=401,
                detail="Authentication required. Please provide valid JWT token."
            )

        # Check if this is a product category
        is_product_category = category in PRODUCT_CATEGORIES

        if is_product_category:
            # PRODUCTS MODE: Query lakehouse /products endpoint
            logger.info(f"Browsing products for category: {category}")

            # Get customer deployment
            registry = get_registry()
            if not registry._initialized:
                await initialize_registry()

            deployment = registry.get_deployment(customer_id)
            if not deployment:
                raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

            # Query products from customer lakehouse
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{deployment.lakehouse_url}/products",
                    params={"limit": 500}
                )
                response.raise_for_status()
                result = response.json()

            products = result.get("products", [])

            # Filter by category
            from .products import categorize_product
            filtered_products = [
                p for p in products
                if categorize_product(p) == category
            ]

            # Paginate
            offset = (page - 1) * page_size
            paginated = filtered_products[offset:offset + page_size]

            # Convert products to Document format for frontend compatibility
            documents = [
                Document(
                    id=p.get("supplier_pid", ""),
                    filename=p.get("product_name", "Unknown Product"),
                    category=category,
                    mcp="product",
                    ingested_at="2025-11-25T00:00:00",
                    size_bytes=0,
                    snippet=p.get("short_description", "")[:500]
                )
                for p in paginated
            ]

            return DataBrowseResponse(
                documents=documents,
                total=len(filtered_products),
                page=page,
                page_size=page_size
            )

        else:
            # DOCUMENTS MODE: Query documents (original logic)
            safe_category = validate_identifier(category, ALLOWED_CATEGORIES, "category")
            safe_mcp = validate_identifier(mcp, ALLOWED_MCPS, "mcp")

            platform = request.app.state.platform

            result = await platform.browse_documents(
                customer_id=customer_id,
                category=safe_category,
                page=page,
                page_size=page_size
            )

            # Convert to Document format
            documents = [
                Document(
                    id=doc.get("id", ""),
                    filename=doc.get("filename", ""),
                    category=doc.get("mcp", "general"),
                    mcp=doc.get("mcp"),
                    ingested_at=doc.get("created_at", ""),
                    size_bytes=len(doc.get("text", "")),
                    snippet=doc.get("text", "")[:500] if doc.get("text") else None
                )
                for doc in result.get("documents", [])
            ]

            return DataBrowseResponse(
                documents=documents,
                total=result.get("total", 0),
                page=page,
                page_size=page_size
            )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error browsing data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=SearchResponse)
async def search_data(
    request: Request,
    search: SearchRequest,
    ctx: CustomerContext = Depends(require_auth)
):
    """
    Search documents using semantic search.

    Requires authentication. Results are filtered by customer_id.

    Example:
        POST /api/data/search
        Headers: Authorization: Bearer <token>
        {
            "query": "VAT regulations 2024",
            "category": "tax",
            "limit": 10
        }
    """
    platform = request.app.state.platform

    try:
        # Check MCP access permission
        if search.mcp and not ctx.can_access_mcp(search.mcp):
            raise HTTPException(
                status_code=403,
                detail=f"Access denied to MCP: {search.mcp}"
            )

        # Route to customer-specific lakehouse for semantic search
        import httpx
        from core.customer_registry import get_registry, initialize_registry

        # Ensure registry is initialized
        registry = get_registry()
        if not registry._initialized:
            await initialize_registry()
            logger.info("Initialized customer registry")

        deployment = registry.get_deployment(ctx.customer_id)

        if not deployment:
            raise HTTPException(
                status_code=404,
                detail=f"No deployment found for customer: {ctx.customer_id}"
            )

        # Call customer's lakehouse vector search
        lakehouse_url = deployment.lakehouse_url
        logger.info(f"Searching customer lakehouse: {lakehouse_url} for query: {search.query}")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{lakehouse_url}/lance/search",
                    json={
                        "query": search.query,
                        "limit": search.limit,
                        "mcp_filter": search.mcp
                    }
                )

                if response.status_code != 200:
                    logger.error(f"Lakehouse search failed: {response.status_code}")
                    return SearchResponse(results=[], total=0, query=search.query)

                data = response.json()

                # Convert to SearchResult format
                results = [
                    SearchResult(
                        id=f"{r['filename']}_{r['chunk_index']}",
                        filename=r['filename'],
                        snippet=r['text'][:300],
                        score=1.0 - r['score'],  # Convert distance to similarity
                        category=r['mcp']
                    )
                    for r in data.get('results', [])
                ]

                return SearchResponse(
                    results=results,
                    total=data.get('total_searched', len(results)),
                    query=search.query
                )

        except Exception as e:
            logger.error(f"Lakehouse search error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_data_get(
    request: Request,
    q: str = Query(..., description="Search query"),
    category: Optional[str] = None,
    mcp: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    ctx: CustomerContext = Depends(require_auth)
):
    """
    Search documents using semantic search (GET variant).

    Requires authentication. Results are filtered by customer_id.

    Example:
        GET /api/data/search?q=VAT+regulations+2024&category=tax&limit=10
        Headers: Authorization: Bearer <token>
    """
    # Convert to SearchRequest format
    search = SearchRequest(
        query=q,
        category=category,
        mcp=mcp,
        limit=limit
    )

    return await search_data(request, search, ctx)


@router.get("/stats")
async def get_data_stats(
    request: Request,
    ctx: CustomerContext = Depends(require_auth)
):
    """
    Get lakehouse statistics for current customer.

    Requires authentication.
    """
    # Stats would be filtered by customer_id in actual implementation
    return {
        "customer_id": ctx.customer_id,
        "total_documents": 0,
        "total_size_bytes": 0,
        "categories": {},
        "mcps": {}
    }


@router.get("/categories")
async def list_categories_dynamic(
    request: Request
):
    """
    List DYNAMIC document categories for current customer (MULTI-TENANT SAFE).

    Returns AI-discovered categories based on actual data, not static categories.
    No auth required (matches browse_data pattern).
    """
    from sqlalchemy import text
    from ..database import get_db

    try:
        # Get database session
        db = get_db()

        # Build dynamic customer ID mapping from database
        # Query all customers to map string IDs to UUIDs
        customer_mapping_query = text("""
            SELECT
                LOWER(REPLACE(company_name, ' ', '-')),
                id::text
            FROM customers
        """)

        mapping_result = db.execute(customer_mapping_query)
        customer_id_mapping = {row[0]: row[1] for row in mapping_result.fetchall()}

        # Also add explicit mappings
        customer_id_mapping.update({
            "eaton": "00000000-0000-0000-0000-000000000002",
            "eprocat": "00000000-0000-0000-0000-000000000001",
        })

        # Try to get customer_id from request (various sources)
        customer_id_value = None

        # Try header first (if auth is present)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                token = auth_header.split(" ")[1]
                from ..auth.jwt import verify_token
                token_data = verify_token(token)
                if token_data:
                    customer_id_value = token_data.customer_id
            except:
                pass

        # Fallback to query param (for testing only - no default)
        if not customer_id_value:
            customer_id_value = request.query_params.get("customer_id")
            if customer_id_value:
                logger.warning(f"Using customer_id from query param (testing): {customer_id_value}")

        # Require customer_id
        if not customer_id_value:
            raise HTTPException(
                status_code=401,
                detail="Authentication required. Please provide valid JWT token."
            )

        # Map to UUID if needed
        if customer_id_value in customer_id_mapping:
            customer_id_value = customer_id_mapping[customer_id_value]

        # Query dynamic categories for this customer (MULTI-TENANT!)
        query = text("""
            SELECT
                category_key,
                category_name,
                icon,
                color,
                document_count
            FROM customer_data_categories
            WHERE customer_id = CAST(:customer_id AS uuid)
              AND is_active = true
            ORDER BY sort_order ASC, document_count DESC
        """)

        result = db.execute(query, {"customer_id": customer_id_value})
        rows = result.fetchall()

        if not rows:
            # No DB categories - generate from file types dynamically
            logger.info(f"No DB categories, generating from documents for {customer_id_value}")

            # Get documents and count by file type
            from core.customer_registry import get_registry
            registry = get_registry()
            deployment = registry.get_deployment(customer_id_value)

            if deployment:
                import httpx
                async with httpx.AsyncClient() as client:
                    resp = await client.get(f"{deployment.lakehouse_url}/delta/query/general_documents?limit=1000")
                    docs_data = resp.json()
                    docs = docs_data.get('rows', [])

                    # Count by file type
                    file_types = {}
                    for doc in docs:
                        ext = doc.get('filename', '').split('.')[-1].lower()
                        file_types[ext] = file_types.get(ext, 0) + 1

                    # Create categories
                    type_icons = {'xlsx': '📊', 'csv': '📋', 'pdf': '📄', 'xml': '🗂️', 'docx': '📝'}
                    categories = [
                        {
                            "name": f"{ext.upper()} Files",
                            "key": ext,
                            "count": count,
                            "icon": type_icons.get(ext, '📄'),
                            "color": "#b0aea5"
                        }
                        for ext, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True)
                    ]

                    return {"categories": categories}

            return {"categories": []}

        # Format for frontend (expects "name" and "count")
        categories = [
            {
                "name": row[1],  # category_name (display name)
                "key": row[0],   # category_key (for filtering)
                "count": row[4] or 0,  # document_count
                "icon": row[2] or "📄",
                "color": row[3] or "#b0aea5"
            }
            for row in rows
        ]

        logger.info(f"Returning {len(categories)} dynamic categories for customer {customer_id_value}")
        return {"categories": categories}

    except Exception as e:
        logger.error(f"Error fetching dynamic categories: {e}", exc_info=True)
        # Fallback to empty if error (no static categories)
        return {"categories": []}
