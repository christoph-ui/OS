"""
Product Tree & Details API

Queries lakehouse for actual product data from eaton_products table.
"""

import logging
import re
import httpx
from typing import List, Dict, Optional
from fastapi import APIRouter, HTTPException, Request, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()

# Product categorization keywords (multi-industry support)
CATEGORY_KEYWORDS = {
    # === LIGHTING PRODUCTS (Lightnet) ===
    "anbau": {
        "id": "anbauleuchten",
        "name": "Anbauleuchten",
        "icon": "💡",
        "keywords": ["anbauleuchte", "anbau", "surface mounted", "deckenleuchte ceiling"]
    },
    "pendel": {
        "id": "pendelleuchten",
        "name": "Pendelleuchten",
        "icon": "🔆",
        "keywords": ["pendelleuchte", "pendel", "pendant", "hängeleuchte", "suspended"]
    },
    "einbau": {
        "id": "einbauleuchten",
        "name": "Einbauleuchten",
        "icon": "⚡",
        "keywords": ["einbauleuchte", "einbau", "recessed", "downlight"]
    },
    "wand": {
        "id": "wandleuchten",
        "name": "Wandleuchten",
        "icon": "🏢",
        "keywords": ["wandleuchte", "wand", "wall", "sconce"]
    },
    "steh": {
        "id": "stehleuchten",
        "name": "Stehleuchten",
        "icon": "🌟",
        "keywords": ["stehleuchte", "steh", "floor lamp", "standleuchte"]
    },

    # === ELECTRICAL PRODUCTS (Eaton, etc.) ===
    "ups": {
        "id": "ups_systems",
        "name": "UPS Systems",
        "icon": "⚡",
        "keywords": ["ups", "uninterruptible power", "backup power", "5e", "5sc"]
    },
    "circuit_breaker": {
        "id": "circuit_breakers",
        "name": "Circuit Breakers",
        "icon": "🔌",
        "keywords": ["circuit breaker", "mcb", "miniature", "faz", "breaker"]
    },
    "rcd": {
        "id": "residual_current",
        "name": "Residual Current Devices",
        "icon": "⚠️",
        "keywords": ["rcd", "rccb", "rcbo", "residual", "frcdm"]
    },
    "fuse": {
        "id": "fuses",
        "name": "Fuses",
        "icon": "🔥",
        "keywords": ["fuse", "fusetron", "limiter", "ann", "ktk"]
    },
    "contactor": {
        "id": "contactors",
        "name": "Contactors & Starters",
        "icon": "🔧",
        "keywords": ["contactor", "magnetic", "motor starter", "dilm"]
    },
    "drive": {
        "id": "drives",
        "name": "Variable Speed Drives",
        "icon": "⚙️",
        "keywords": ["drive", "vfd", "frequency", "inverter", "de1"]
    },
    "switch": {
        "id": "switches",
        "name": "Switches & Controls",
        "icon": "🔘",
        "keywords": ["switch", "control", "emergency", "palm", "fak"]
    }
}


class ProductTreeResponse(BaseModel):
    categories: List[Dict]
    total_products: int


class ProductDetailsResponse(BaseModel):
    product_code: str
    name: str
    description: str
    specifications: Dict
    documents: List[Dict]
    applicable_tools: List[Dict]


async def query_lakehouse_products(customer_id: str, limit: int = 500, search: str = None) -> Dict:
    """
    Query products from customer-specific lakehouse API (MULTI-TENANT SAFE).

    Args:
        customer_id: Customer identifier
        limit: Max products to return
        search: Optional search filter

    Returns:
        Products from customer's lakehouse

    Raises:
        HTTPException: If lakehouse unavailable or customer not found
    """
    from core.customer_registry import get_registry, initialize_registry

    try:
        # Ensure registry is initialized
        registry = get_registry()
        if not registry._initialized:
            await initialize_registry()
            logger.info("Initialized customer registry")

        # Get customer-specific deployment
        deployment = registry.get_deployment(customer_id)

        if not deployment:
            raise HTTPException(
                status_code=404,
                detail=f"No deployment found for customer: {customer_id}"
            )

        lakehouse_url = deployment.lakehouse_url
        logger.info(f"Querying lakehouse for {customer_id} at {lakehouse_url}")

        # Query customer's lakehouse
        async with httpx.AsyncClient(timeout=30.0) as client:
            params = {"limit": limit}
            if search:
                params["search"] = search

            response = await client.get(f"{lakehouse_url}/products", params=params)
            response.raise_for_status()
            return response.json()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to query lakehouse for {customer_id}: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Lakehouse unavailable: {str(e)}"
        )


def categorize_product(product: Dict) -> str:
    """
    Categorize product based on name and keywords.

    Returns category_id or 'other' if no match.
    """
    product_name = (product.get("product_name", "") or "").lower()
    product_desc = (product.get("short_description", "") or "").lower()
    supplier_pid = (product.get("supplier_pid", "") or "").lower()

    # Combined search text
    search_text = f"{product_name} {product_desc} {supplier_pid}"

    # Match against category keywords
    for cat_key, cat_data in CATEGORY_KEYWORDS.items():
        for keyword in cat_data["keywords"]:
            if keyword.lower() in search_text:
                return cat_data["id"]

    return "other"


@router.get("/tree", response_model=ProductTreeResponse)
async def get_product_tree(
    request: Request,
    customer_id: Optional[str] = Query(default=None)
):
    """
    Build product tree from lakehouse products table (MULTI-TENANT SAFE).

    Returns hierarchical tree with:
    - Auto-categorized by product type
    - Grouped by product family
    - Product counts per category
    - Routed to customer-specific lakehouse
    """
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

        from core.customer_registry import get_registry, initialize_registry

        # Get customer deployment
        registry = get_registry()
        if not registry._initialized:
            await initialize_registry()

        deployment = registry.get_deployment(customer_id)
        if not deployment:
            raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

        # Try to get categories from lakehouse /products/categories endpoint (3-level hierarchy)
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{deployment.lakehouse_url}/products/categories")

                if response.status_code == 200:
                    data = response.json()
                    # Lakehouse categories endpoint returns exactly what we need
                    return ProductTreeResponse(
                        categories=data.get("categories", []),
                        total_products=data.get("total_products", 0)
                    )
        except Exception as e:
            logger.warning(f"/products/categories not available, falling back to keyword-based: {e}")

        # Fallback: Query products and build tree with keyword categorization
        try:
            result = await query_lakehouse_products(customer_id=customer_id, limit=10000)
            products = result.get("products", [])
        except Exception as e:
            logger.warning(f"/products endpoint not available, trying products_documents table: {e}")

            # Fallback: Query products_documents table directly
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{deployment.lakehouse_url}/delta/query/products_documents",
                    params={"limit": 500}
                )

                if response.status_code == 200:
                    data = response.json()
                    # Convert products_documents rows to products format
                    products = [{"product_name": row.get("filename", ""), "supplier_pid": row.get("id", "")} for row in data.get("rows", [])]
                else:
                    products = []

        if not products:
            return ProductTreeResponse(
                categories=[],
                total_products=0
            )

        # Build tree with keyword-based categories
        tree = build_product_tree_from_products(products)

        return ProductTreeResponse(
            categories=tree["categories"],
            total_products=len(products)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error building product tree: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_products(
    request: Request,
    customer_id: Optional[str] = Query(default=None),
    product_family: Optional[str] = Query(default=None),
    color_temperature: Optional[str] = Query(default=None),
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0)
):
    """
    List products with optional filters.

    Filters:
    - product_family: Filter by family (e.g., "Caleo", "Matric")
    - color_temperature: Filter by temp (e.g., "3000K", "4000K")
    - limit: Max products to return
    - offset: Pagination offset
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

        # Query lakehouse products with filters
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(
                f"{deployment.lakehouse_url}/products",
                params={"limit": 10000}  # Use /products endpoint instead
            )
            response.raise_for_status()
            data = response.json()

        products = data.get("products", [])

        # Apply filters
        if product_family:
            # Filter by family using same extract logic
            def matches_family(p):
                product_name = (p.get('product_name', '') or '').lower()
                short_desc = (p.get('short_description', '') or '').lower()
                search_text = f"{product_name} {short_desc}"
                return product_family.lower() in search_text

            products = [p for p in products if matches_family(p)]

        if color_temperature and color_temperature != 'Other':
            products = [p for p in products if (p.get('color_temperature', '') or '') == color_temperature]

        total = len(products)
        products = products[offset:offset+limit]

        return {
            "products": products,
            "total": total,
            "limit": limit,
            "offset": offset,
            "filters": {
                "product_family": product_family,
                "color_temperature": color_temperature
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing products: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{product_code}", response_model=ProductDetailsResponse)
async def get_product_details(
    request: Request,
    product_code: str,
    customer_id: Optional[str] = Query(default=None)
):
    """
    Get complete details for a specific product (MULTI-TENANT SAFE).

    Returns:
    - Technical specifications from lakehouse
    - Product images
    - Compliance data
    - Applicable MCP tools
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

        # Query product from lakehouse using search endpoint
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Use dedicated search endpoint (fast SKU lookup)
            response = await client.get(
                f"{deployment.lakehouse_url}/products/search/{product_code}"
            )

            if response.status_code == 200:
                data = response.json()
                product = data.get("product", {})
                images = []
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"Product {product_code} not found"
                )

        # Parse specifications for THIS customer's products
        specs = {
            "sku": product.get("sku", ""),
            "product_family": product.get("product_family", ""),
            "installation_type": product.get("installation_type", ""),
            "light_distribution": product.get("light_distribution", ""),
            "light_source": product.get("light_source", ""),
            "optical_system": product.get("optical_system", ""),
            "surface_finish": product.get("surface", ""),
            "control_type": product.get("control", ""),
            "color_rendering_index": product.get("color_rendering_index", ""),
            "color_temperature": product.get("color_temperature", ""),
            "power_mode": product.get("power_mode", ""),
            "form": product.get("form", ""),
            "length_mm": product.get("length_mm", ""),
            "width_mm": product.get("width_mm", ""),
            "height_mm": product.get("height_mm", ""),
            "luminous_flux": product.get("luminous_flux", ""),
            "power_consumption": product.get("power_consumption", ""),
            "weight": product.get("weight_kg", ""),
            "protection_class_ip": product.get("protection_class_ip", ""),
            "protection_class": product.get("protection_class", ""),
            "led_lifetime": product.get("led_lifetime", ""),
            "photometric_code": product.get("photometric_code", ""),
            "ik_value": product.get("ik_value", ""),
            "certification": product.get("certification", ""),
            "voltage": product.get("voltage", ""),
            "frequency": product.get("frequency", ""),
            "manufacturer": product.get("manufacturer", ""),
            "brand": product.get("brand", "")
        }

        # Parse specifications JSON if available
        if product.get("specifications"):
            import json
            try:
                spec_dict = json.loads(product["specifications"]) if isinstance(product["specifications"], str) else product["specifications"]
                specs["technical_specs"] = spec_dict
            except:
                pass

        # Determine applicable tools
        tools = get_applicable_tools(product_code, specs)

        # Format images as documents
        documents = []
        for img in images[:10]:
            documents.append({
                "filename": img.get("image_filename", ""),
                "type": "image",
                "url": img.get("image_url", "")
            })

        return ProductDetailsResponse(
            product_code=product.get("sku", product_code),
            name=product.get("product_name", product_code),
            description=product.get("long_description") or product.get("short_description", ""),
            specifications=specs,
            documents=documents,
            applicable_tools=tools
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching product details: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def build_product_tree_from_products(products: List[Dict]) -> Dict:
    """
    Build product tree from actual products data.

    Categorizes by product type (UPS, Circuit Breakers, Fuses, etc.)
    """
    tree = {"categories": []}
    products_by_category = {}

    # Initialize categories with icons
    for cat_key, cat_data in CATEGORY_KEYWORDS.items():
        products_by_category[cat_data["id"]] = {
            "id": cat_data["id"],
            "name": cat_data["name"],
            "icon": cat_data["icon"],
            "products": [],
            "count": 0
        }

    # Add "other" category
    products_by_category["other"] = {
        "id": "other",
        "name": "Other Products",
        "icon": "📦",
        "products": [],
        "count": 0
    }

    # Categorize products
    for product in products:
        category_id = categorize_product(product)

        # Add to category with proper SKU/code mapping
        product_code = product.get("sku") or product.get("supplier_pid", "")

        products_by_category[category_id]['products'].append({
            "code": product_code,  # Frontend expects 'code' field
            "sku": product.get("sku", ""),
            "name": product.get("product_name", "Unknown"),
            "product_name": product.get("product_name", "Unknown"),
            "short_description": product.get("short_description", ""),
            "product_family": product.get("product_family", ""),
            "price_eur": product.get("price_eur", ""),
            "manufacturer": product.get("manufacturer", product.get("manufacturer_name", "")),
            "brand": product.get("brand", ""),
            "specs": {
                "sku": product.get("sku", ""),
                "product_family": product.get("product_family", ""),
                "manufacturer": product.get("manufacturer", ""),
                "color_temperature": product.get("color_temperature", ""),
                "luminous_flux": product.get("luminous_flux", ""),
                "power_consumption": product.get("power_consumption", "")
            }
        })
        products_by_category[category_id]['count'] += 1

    # Remove empty categories and convert to list
    tree['categories'] = [
        cat for cat in products_by_category.values()
        if cat['count'] > 0
    ]

    # Sort by count descending
    tree['categories'].sort(key=lambda x: x['count'], reverse=True)

    return tree


def extract_product_code(text: str) -> Optional[str]:
    """Extract product code from ECLASS text."""
    # Look for MANUFACTURER_TYPE_DESCR or MANUFACTURER_PID
    match = re.search(r'MANUFACTURER_TYPE_DESCR:\s*(\S+)', text)
    if match:
        return match.group(1)

    match = re.search(r'MANUFACTURER_PID:\s*(\S+)', text)
    if match:
        return match.group(1)

    return None


def extract_eclass_code(text: str) -> Optional[str]:
    """Extract ECLASS classification code."""
    match = re.search(r'REFERENCE_FEATURE_GROUP_ID:\s*(\d+)', text)
    return match.group(1) if match else None


def extract_product_name(text: str) -> str:
    """Extract product name/description."""
    match = re.search(r'MANUFACTURER_NAME:\s*(.+?)(?:\n|$)', text)
    return match.group(1).strip() if match else "Unknown Product"


def extract_quick_specs(text: str) -> Dict:
    """Extract key specifications for quick display."""
    specs = {}

    # Extract voltage (FT_ID: 0173-1#02-AAB491#008)
    match = re.search(r'FT_ID:\s*0173-1#02-AAB491#008.*?FVALUE:\s*([\d.]+)', text, re.DOTALL)
    if match:
        specs['voltage'] = f"{match.group(1)}V"

    # Extract current (FT_ID: 0173-1#02-AAF726#003)
    match = re.search(r'FT_ID:\s*0173-1#02-AAF726#003.*?FVALUE:\s*([\d.]+)', text, re.DOTALL)
    if match:
        specs['current'] = f"{match.group(1)}A"

    # Extract poles (FT_ID: 0173-1#02-AAG286#003)
    match = re.search(r'FT_ID:\s*0173-1#02-AAG286#003.*?FVALUE:\s*([\d.]+)', text, re.DOTALL)
    if match:
        specs['poles'] = int(float(match.group(1)))

    return specs


def parse_eclass_features(text: str) -> Dict:
    """Parse all ECLASS features into structured data."""
    specs = {
        "name": extract_product_name(text),
        "description": "",
        "features": {}
    }

    # Extract description
    match = re.search(r'MANUFACTURER_TYPE_DESCR:\s*(.+?)(?:\n|$)', text)
    if match:
        specs["description"] = match.group(1).strip()

    # Extract all FT_ID/FVALUE pairs
    ft_matches = re.finditer(
        r'FT_ID:\s*([\w#-]+).*?FVALUE:\s*([^\n]+)',
        text,
        re.DOTALL
    )

    for match in ft_matches:
        ft_id = match.group(1)
        value = match.group(2).strip()
        specs["features"][ft_id] = value

    # Add quick specs
    specs.update(extract_quick_specs(text))

    return specs


def get_applicable_tools(product_code: str, specs: Dict) -> List[Dict]:
    """Determine which MCP tools apply to this product."""
    tools = []

    # Detect industry and set appropriate competitors
    manufacturer = specs.get("manufacturer", "").lower()

    if "lightnet" in manufacturer:
        competitors = "Osram, Philips Lighting, Trilux, Zumtobel, Regent"
        industry = "LED lighting"
    elif "eaton" in manufacturer:
        competitors = "ABB, Siemens, Schneider Electric"
        industry = "electrical equipment"
    else:
        # Generic - let AI determine competitors
        competitors = "market leaders"
        industry = "product category"

    # MARKET MCP tools (applicable to all products)
    tools.extend([
        {
            "id": "market_analyze_competitors",
            "name": "Analyze vs Competitors",
            "description": f"Compare against {competitors}",
            "icon": "🔍",
            "mcp": "market",
            "query_template": f"Analyze {product_code} vs competitors in {industry}: {competitors}"
        },
        {
            "id": "market_pricing_intel",
            "name": "Pricing Intelligence",
            "description": "Market pricing analysis",
            "icon": "💰",
            "mcp": "market",
            "query_template": f"Analyze market pricing for {product_code}"
        },
        {
            "id": "market_alternatives",
            "name": "Find Alternatives",
            "description": "Discover alternative products",
            "icon": "🏢",
            "mcp": "market",
            "query_template": f"Find alternatives to {product_code}"
        },
        {
            "id": "market_coverage",
            "name": "Market Coverage",
            "description": "Analyze market coverage and positioning",
            "icon": "🌍",
            "mcp": "market",
            "query_template": f"Analyze market coverage for {product_code}"
        }
    ])

    # PUBLISH MCP tools (applicable to all products)
    tools.extend([
        {
            "id": "publish_amazon",
            "name": "Amazon Listing",
            "description": "Generate Amazon product listing",
            "icon": "🛒",
            "mcp": "publish",
            "query_template": f"Create Amazon listing for {product_code}"
        },
        {
            "id": "publish_datasheet",
            "name": "Datasheet PDF",
            "description": "Generate technical datasheet",
            "icon": "📄",
            "mcp": "publish",
            "query_template": f"Generate datasheet for {product_code}"
        },
        {
            "id": "publish_linkedin",
            "name": "LinkedIn Post",
            "description": "Create LinkedIn product announcement",
            "icon": "💼",
            "mcp": "publish",
            "query_template": f"Create LinkedIn post for {product_code}"
        },
        {
            "id": "publish_bmecat",
            "name": "BMEcat Export",
            "description": "Export BMEcat catalog feed",
            "icon": "📦",
            "mcp": "publish",
            "query_template": f"Export BMEcat for {product_code}"
        }
    ])

    return tools
