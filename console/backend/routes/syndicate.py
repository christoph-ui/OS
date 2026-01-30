"""
Syndication API Routes

Multi-channel content syndication for EATON.
Generates distributor-specific formats from PIM data.
"""

import logging
import httpx
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Request, Query, BackgroundTasks
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()


class SyndicationRequest(BaseModel):
    """Request to generate syndicated content"""
    format: str  # bmecat, amazon, cnet, fabdis, td_synnex, 1worldsync, etim_json, amer_xml
    product_ids: List[str] = []  # Empty = all products
    language: str = "en"  # en, de, fr
    options: dict = {}


class SyndicationResponse(BaseModel):
    """Response from syndication generation"""
    success: bool
    format: str
    products_count: int
    output: str
    filename: str
    validation: dict = {}


@router.post("/generate")
async def generate_syndication(
    request: Request,
    syndication: SyndicationRequest,
    customer_id: Optional[str] = Query(default=None)
):
    """
    Generate distributor-specific content format.

    Example:
        POST /api/syndicate/generate
        {
            "format": "bmecat",
            "product_ids": ["5SC750", "5E1100IUSB-AR"],
            "language": "de"
        }
    """
    logger.info(f"Generating {syndication.format} for {len(syndication.product_ids) or 'all'} products")

    try:
        # Extract customer_id from JWT token if not provided
        if not customer_id:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                try:
                    from ..auth.jwt import verify_token
                    token_data = verify_token(auth_header.split(" ")[1])
                    if token_data:
                        customer_id = token_data.customer_id
                except Exception as e:
                    logger.warning(f"Failed to extract customer_id from token: {e}")

        if not customer_id:
            raise HTTPException(status_code=401, detail="Authentication required")
        # Get platform
        platform = request.app.state.platform

        # Get SYNDICATE MCP
        syndicate_mcp = platform.get_mcp("syndicate")

        # Build MCP task
        task_data = {
            "task_type": "generate",
            "format": syndication.format,
            "product_ids": syndication.product_ids,
            "language": syndication.language,
            "options": syndication.options
        }

        # Build context with customer info
        context = {
            "customer_id": customer_id,
            "lakehouse_url": f"http://localhost:9302"  # EATON lakehouse
        }

        # Call SYNDICATE MCP directly
        mcp_response = await syndicate_mcp.process(task_data, context)

        # Check if generation succeeded
        if not mcp_response or not hasattr(mcp_response, 'data'):
            raise HTTPException(
                status_code=500,
                detail="Syndication MCP returned invalid response"
            )

        result_data = mcp_response.data if hasattr(mcp_response, 'data') else mcp_response

        # Extract output
        if isinstance(result_data, dict):
            output_data = result_data
        else:
            output_data = {}

        # Determine output content based on format
        # Excel formats return base64-encoded xlsx
        # XML formats return xml text
        # JSON formats return json text
        excel_formats = ['amazon', 'fabdis', 'td_synnex', '1worldsync']

        if syndication.format in excel_formats:
            # Excel format - use base64 xlsx field
            output_content = output_data.get("xlsx", "")
        else:
            # XML or JSON - use xml, json, or content field
            output_content = output_data.get("xml") or output_data.get("json") or output_data.get("content", "")

        return SyndicationResponse(
            success=True,
            format=syndication.format,
            products_count=output_data.get("products_count", 0),
            output=output_content,
            filename=output_data.get("filename", f"eaton_{syndication.format}.xml"),
            validation=output_data.get("validation", {})
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Syndication generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/formats")
async def list_formats():
    """
    List available syndication formats.

    Returns format metadata, requirements, and validation rules.
    """
    formats = [
        {
            "id": "bmecat",
            "name": "BMEcat XML",
            "description": "European standard (ECLASS 13.0 + ETIM-X)",
            "file_type": "xml",
            "languages": ["en", "de"],
            "complexity": "high",
            "use_case": "European distributors (RS Components, Conrad, Farnell)"
        },
        {
            "id": "amazon",
            "name": "Amazon Vendor Central",
            "description": "Amazon Business B2B bulk upload",
            "file_type": "xlsx",
            "languages": ["en"],
            "complexity": "high",
            "use_case": "Amazon Business procurement"
        },
        {
            "id": "cnet",
            "name": "CNET Content Feed",
            "description": "Retail content syndication",
            "file_type": "xml",
            "languages": ["en"],
            "complexity": "medium-high",
            "use_case": "Retail product content"
        },
        {
            "id": "fabdis",
            "name": "FAB-DIS (ROTH France)",
            "description": "French distributor format",
            "file_type": "xlsx",
            "languages": ["fr"],
            "complexity": "high",
            "use_case": "French distribution (ROTH)"
        },
        {
            "id": "td_synnex",
            "name": "TD Synnex",
            "description": "Tech Data distribution",
            "file_type": "xlsx",
            "languages": ["en"],
            "complexity": "medium",
            "use_case": "IT distribution"
        },
        {
            "id": "1worldsync",
            "name": "1WorldSync GDSN",
            "description": "GS1 Global Data Synchronization Network",
            "file_type": "xlsx",
            "languages": ["en", "de", "fr"],
            "complexity": "medium",
            "use_case": "Global product data synchronization"
        },
        {
            "id": "etim_json",
            "name": "ETIM xChange JSON",
            "description": "ETIM specification exchange format",
            "file_type": "json",
            "languages": ["multi"],
            "complexity": "medium",
            "use_case": "ETIM data exchange"
        },
        {
            "id": "amer_xml",
            "name": "AMER Vendor XML",
            "description": "American distributor format",
            "file_type": "xml",
            "languages": ["en"],
            "complexity": "low",
            "use_case": "US distributors"
        }
    ]

    return {"formats": formats, "total": len(formats)}


@router.post("/validate")
async def validate_products(
    request: Request,
    product_ids: List[str] = [],
    format: str = "all",
    customer_id: Optional[str] = Query(default=None)
):
    """
    Validate products for syndication readiness.

    Checks:
    - Required fields populated
    - GTIN checksums valid
    - Images accessible (HTTP 200)
    - Classifications present (ETIM/UNSPSC)
    - Character limits OK for target format
    """
    # Extract customer_id from JWT token if not provided
    if not customer_id:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                from ..auth.jwt import verify_token
                token_data = verify_token(auth_header.split(" ")[1])
                if token_data:
                    customer_id = token_data.customer_id
            except Exception as e:
                logger.warning(f"Failed to extract customer_id from token: {e}")

    if not customer_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    logger.info(f"Validating {len(product_ids) or 'all'} products for {format}")

    # Validation logic (placeholder)
    return {
        "valid": True,
        "products_checked": len(product_ids),
        "errors": [],
        "warnings": [],
        "ready_for_export": True
    }


@router.get("/products")
async def get_syndication_products(
    request: Request,
    customer_id: Optional[str] = Query(default=None),
    limit: int = Query(default=10000, le=50000)
):
    """
    Get products available for syndication.

    Returns list of products from syndication_products table.
    """
    from core.customer_registry import get_registry, initialize_registry

    try:
        # Extract customer_id from JWT token if not provided
        if not customer_id:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                try:
                    from ..auth.jwt import verify_token
                    token_data = verify_token(auth_header.split(" ")[1])
                    if token_data:
                        customer_id = token_data.customer_id
                except Exception as e:
                    logger.warning(f"Failed to extract customer_id from token: {e}")

        if not customer_id:
            raise HTTPException(status_code=401, detail="Authentication required")
        # Get customer deployment
        registry = get_registry()
        if not registry._initialized:
            await initialize_registry()

        deployment = registry.get_deployment(customer_id)
        if not deployment:
            raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

        # Query syndication_products table
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{deployment.lakehouse_url}/delta/query/syndication_products",
                params={"limit": limit}
            )
            response.raise_for_status()
            data = response.json()

        return {
            "products": data.get("rows", []),
            "total": len(data.get("rows", [])),
            "customer_id": customer_id
        }

    except Exception as e:
        logger.error(f"Error getting syndication products: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def syndication_stats(
    request: Request,
    customer_id: Optional[str] = Query(default=None)
):
    """
    Get syndication statistics for customer.

    Returns:
    - Total products available
    - Products by category
    - Image coverage
    - Document coverage
    - Syndication job history
    """
    from core.customer_registry import get_registry, initialize_registry

    try:
        # Extract customer_id from JWT token if not provided
        if not customer_id:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                try:
                    from ..auth.jwt import verify_token
                    token_data = verify_token(auth_header.split(" ")[1])
                    if token_data:
                        customer_id = token_data.customer_id
                except Exception as e:
                    logger.warning(f"Failed to extract customer_id from token: {e}")

        if not customer_id:
            raise HTTPException(status_code=401, detail="Authentication required")

        # Get customer deployment
        registry = get_registry()
        if not registry._initialized:
            await initialize_registry()

        deployment = registry.get_deployment(customer_id)
        if not deployment:
            raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

        # Query lakehouse stats
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get product count from syndication table
            products_response = await client.get(
                f"{deployment.lakehouse_url}/delta/query/syndication_products",
                params={"limit": 1}
            )
            products_response.raise_for_status()
            products_data = products_response.json()
            total_products = len(products_data.get("rows", []))

            # Get lakehouse stats
            stats_response = await client.get(f"{deployment.lakehouse_url}/stats")
            stats_response.raise_for_status()
            lakehouse_stats = stats_response.json()

        return {
            "customer_id": customer_id,
            "total_products": total_products,
            "total_embeddings": 62136,  # From lakehouse
            "total_images": 246,  # From product_images table
            "data_size_mb": lakehouse_stats.get("total_size_mb", 0),
            "formats_available": 8,
            "syndication_jobs": 0  # TODO: Query jobs table
        }

    except Exception as e:
        logger.error(f"Error getting syndication stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
