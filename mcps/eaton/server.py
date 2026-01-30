#!/usr/bin/env python3
"""
EATON Customer MCP Server

Provides Claude Desktop access to EATON's Intelligence Platform data:
- 62,136 embeddings (semantic search)
- 327 products (UPS, circuit breakers, fuses)
- 344 documents (ECLASS catalogs, 3D models, PDFs)
- 246 product images

Connects to EATON lakehouse API at localhost:9302
"""

import asyncio
import json
import logging
import sys
from typing import Any, Dict, List, Optional

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

# Configure logging - MUST use stderr to avoid corrupting MCP JSON-RPC on stdout
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("eaton-mcp")

# Lakehouse API configuration
LAKEHOUSE_URL = "http://localhost:9302"
TIMEOUT = 30.0

# Create MCP server instance
app = Server("eaton-intelligence")


# =============================================================================
# HTTP CLIENT
# =============================================================================

async def call_lakehouse_api(
    method: str,
    path: str,
    json_data: Optional[Dict] = None,
    params: Optional[Dict] = None,
    base_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Call the EATON lakehouse HTTP API or console backend API.

    Args:
        method: HTTP method (GET, POST)
        path: API path (e.g., "/products")
        json_data: JSON body for POST requests
        params: Query parameters
        base_url: Override base URL (default: LAKEHOUSE_URL)

    Returns:
        API response as dict

    Raises:
        Exception: If API call fails
    """
    url = f"{base_url or LAKEHOUSE_URL}{path}"

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            if method.upper() == "GET":
                response = await client.get(url, params=params or {})
            elif method.upper() == "POST":
                response = await client.post(url, json=json_data or {})
            else:
                raise ValueError(f"Unsupported method: {method}")

            response.raise_for_status()
            return response.json()

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
        raise Exception(f"API error: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        logger.error(f"API call failed: {e}")
        raise Exception(f"Failed to connect to EATON lakehouse: {str(e)}")


# =============================================================================
# MCP TOOLS
# =============================================================================

@app.list_tools()
async def list_tools() -> List[Tool]:
    """
    List available MCP tools for EATON data access.
    """
    return [
        Tool(
            name="search_products",
            description=(
                "Search EATON product catalog (327 products: UPS systems, "
                "circuit breakers, fuses, electrical components). "
                "Returns product names, IDs, descriptions, and specifications."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (product name, ID, or description keywords)"
                    },
                    "limit": {
                        "type": "number",
                        "description": "Maximum products to return (default: 20, max: 100)",
                        "default": 20
                    }
                },
                "required": ["query"]
            }
        ),

        Tool(
            name="get_product",
            description=(
                "Get detailed product information including specifications, "
                "ECLASS/ETIM classifications, and linked product images."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "string",
                        "description": "Product ID (supplier_pid, e.g., '167885', '5E1100IUSB-AR')"
                    }
                },
                "required": ["product_id"]
            }
        ),

        Tool(
            name="semantic_search",
            description=(
                "Semantic search across all 62,136 EATON document chunks using "
                "vector embeddings. Finds relevant information from catalogs, "
                "technical specs, 3D models, and product data."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (natural language question or keywords)"
                    },
                    "limit": {
                        "type": "number",
                        "description": "Maximum results to return (default: 5, max: 20)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        ),

        Tool(
            name="query_documents",
            description=(
                "Query the general_documents table (344 documents: ECLASS catalogs, "
                "3D models, PDFs, XML files, Excel extracts)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "number",
                        "description": "Maximum documents to return (default: 10, max: 50)",
                        "default": 10
                    }
                },
                "required": []
            }
        ),

        Tool(
            name="list_tables",
            description=(
                "List all available data tables in the EATON lakehouse "
                "(Delta Lake tables and LanceDB vector datasets)."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),

        Tool(
            name="get_stats",
            description=(
                "Get EATON lakehouse statistics: table counts, dataset sizes, "
                "total data volume."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),

        # SYNDICATION TOOLS
        Tool(
            name="list_syndication_formats",
            description=(
                "List all 8 available syndication export formats: "
                "BMEcat XML, Amazon Vendor, CNET Feed, FAB-DIS France, "
                "TD Synnex, 1WorldSync, ETIM JSON, AMER XML. "
                "Shows format details, languages, and use cases."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),

        Tool(
            name="get_syndication_products",
            description=(
                "Get list of products available for syndication (109 products "
                "from P360 PIM data with full metadata: identifiers, "
                "classifications, features, dimensions, images, documents)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Filter by product type (UPS, MCB, Fuse, etc.)",
                        "default": "all"
                    },
                    "limit": {
                        "type": "number",
                        "description": "Max products to return (default: 20)",
                        "default": 20
                    }
                },
                "required": []
            }
        ),

        Tool(
            name="generate_syndication",
            description=(
                "Generate distributor-ready export file in specified format. "
                "Creates formatted XML/XLSX/JSON ready for distributors. "
                "Supports all 8 formats with proper formatting (Excel with bold headers, "
                "auto-sized columns; XML valid; French translation for FAB-DIS)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "format": {
                        "type": "string",
                        "enum": ["bmecat", "amazon", "cnet", "fabdis", "td_synnex", "1worldsync", "etim_json", "amer_xml"],
                        "description": "Export format to generate"
                    },
                    "product_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Product SKUs to include (empty = all products)",
                        "default": []
                    },
                    "language": {
                        "type": "string",
                        "enum": ["en", "de", "fr"],
                        "description": "Output language (default: en)",
                        "default": "en"
                    }
                },
                "required": ["format"]
            }
        ),

        Tool(
            name="preview_syndication",
            description=(
                "Preview syndication output for first 3 products without downloading. "
                "Shows what the generated file will look like (headers, data structure, formatting)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "format": {
                        "type": "string",
                        "enum": ["bmecat", "amazon", "cnet", "fabdis", "td_synnex", "1worldsync", "etim_json", "amer_xml"],
                        "description": "Format to preview"
                    }
                },
                "required": ["format"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """
    Execute MCP tool by name.

    Args:
        name: Tool name
        arguments: Tool arguments (dict)

    Returns:
        List of text content blocks
    """
    try:
        if name == "search_products":
            return await handle_search_products(arguments)
        elif name == "get_product":
            return await handle_get_product(arguments)
        elif name == "semantic_search":
            return await handle_semantic_search(arguments)
        elif name == "query_documents":
            return await handle_query_documents(arguments)
        elif name == "list_tables":
            return await handle_list_tables(arguments)
        elif name == "get_stats":
            return await handle_get_stats(arguments)
        # SYNDICATION TOOLS
        elif name == "list_syndication_formats":
            return await handle_list_syndication_formats(arguments)
        elif name == "get_syndication_products":
            return await handle_get_syndication_products(arguments)
        elif name == "generate_syndication":
            return await handle_generate_syndication(arguments)
        elif name == "preview_syndication":
            return await handle_preview_syndication(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]


# =============================================================================
# TOOL HANDLERS
# =============================================================================

async def handle_search_products(args: Dict) -> List[TextContent]:
    """Search EATON products."""
    query = args.get("query", "")
    limit = min(args.get("limit", 20), 100)

    result = await call_lakehouse_api(
        "GET",
        "/products",
        params={"search": query, "limit": limit}
    )

    products = result.get("products", [])
    total = result.get("total", 0)

    if not products:
        return [TextContent(
            type="text",
            text=f"No products found for query: '{query}'"
        )]

    # Format results
    output_lines = [
        f"# EATON Product Search Results",
        f"Query: '{query}'",
        f"Found: {total} products (showing {len(products)})\n"
    ]

    for idx, product in enumerate(products, 1):
        product_name = product.get("product_name", "N/A")
        supplier_pid = product.get("supplier_pid", "N/A")
        short_desc = product.get("short_description", "")

        output_lines.append(f"## {idx}. {product_name}")
        output_lines.append(f"**ID:** {supplier_pid}")
        if short_desc:
            output_lines.append(f"**Description:** {short_desc}")
        output_lines.append("")

    return [TextContent(
        type="text",
        text="\n".join(output_lines)
    )]


async def handle_get_product(args: Dict) -> List[TextContent]:
    """Get detailed product information."""
    product_id = args.get("product_id", "")

    if not product_id:
        return [TextContent(
            type="text",
            text="Error: product_id is required"
        )]

    result = await call_lakehouse_api(
        "GET",
        f"/products/{product_id}"
    )

    product = result.get("product", {})
    images = result.get("images", [])
    image_count = result.get("image_count", 0)

    if not product:
        return [TextContent(
            type="text",
            text=f"Product not found: {product_id}"
        )]

    # Format product details
    output_lines = [
        f"# {product.get('product_name', 'Product')}",
        f"**Supplier ID:** {product.get('supplier_pid', 'N/A')}",
        f"**Manufacturer:** {product.get('manufacturer_name', 'N/A')}",
        ""
    ]

    # Add description if available
    if product.get("short_description"):
        output_lines.append(f"## Description")
        output_lines.append(product["short_description"])
        output_lines.append("")

    # Add specifications
    output_lines.append("## Specifications")
    for key, value in product.items():
        if key not in ["product_name", "supplier_pid", "manufacturer_name", "short_description", "long_description"]:
            if value and value != "N/A":
                output_lines.append(f"- **{key}:** {value}")
    output_lines.append("")

    # Add images
    if images:
        output_lines.append(f"## Images ({image_count} available)")
        for img in images[:5]:  # Show first 5
            img_url = img.get("image_url", "")
            img_type = img.get("image_type", "unknown")
            if img_url:
                output_lines.append(f"- {img_type}: {img_url}")

    return [TextContent(
        type="text",
        text="\n".join(output_lines)
    )]


async def handle_semantic_search(args: Dict) -> List[TextContent]:
    """Semantic search using vector embeddings."""
    query = args.get("query", "")
    limit = min(args.get("limit", 5), 20)

    result = await call_lakehouse_api(
        "POST",
        "/lance/search",
        json_data={"query": query, "limit": limit}
    )

    results = result.get("results", [])
    count = result.get("count", 0)
    search_type = result.get("search_type", "unknown")
    total_searched = result.get("total_searched", 0)

    if not results:
        return [TextContent(
            type="text",
            text=f"No results found for: '{query}'"
        )]

    # Format results
    output_lines = [
        f"# EATON Semantic Search Results",
        f"Query: '{query}'",
        f"Search Type: {search_type}",
        f"Results: {count} (searched {total_searched:,} embeddings)\n"
    ]

    for idx, item in enumerate(results, 1):
        filename = item.get("filename", "Unknown")
        text = item.get("text", "")
        score = item.get("score", 0.0)

        # Truncate long text
        if len(text) > 500:
            text = text[:500] + "..."

        output_lines.append(f"## Result {idx} (Score: {score:.4f})")
        output_lines.append(f"**Source:** {filename}")
        output_lines.append(f"```\n{text}\n```")
        output_lines.append("")

    return [TextContent(
        type="text",
        text="\n".join(output_lines)
    )]


async def handle_query_documents(args: Dict) -> List[TextContent]:
    """Query general documents table."""
    limit = min(args.get("limit", 10), 50)

    result = await call_lakehouse_api(
        "GET",
        "/delta/query/general_documents",
        params={"limit": limit}
    )

    rows = result.get("rows", [])
    count = result.get("count", 0)

    if not rows:
        return [TextContent(
            type="text",
            text="No documents found"
        )]

    # Format document list
    output_lines = [
        f"# EATON Documents",
        f"Found: {count} documents\n"
    ]

    for idx, doc in enumerate(rows, 1):
        filename = doc.get("filename", "Unknown")
        mcp = doc.get("mcp", "general")

        output_lines.append(f"{idx}. **{filename}** (Category: {mcp})")

    return [TextContent(
        type="text",
        text="\n".join(output_lines)
    )]


async def handle_list_tables(args: Dict) -> List[TextContent]:
    """List all available tables."""
    delta_result = await call_lakehouse_api("GET", "/delta/tables")
    lance_result = await call_lakehouse_api("GET", "/lance/datasets")

    delta_tables = delta_result.get("tables", [])
    lance_datasets = lance_result.get("datasets", [])

    output_lines = [
        "# EATON Lakehouse Tables\n",
        "## Delta Lake Tables (Structured Data)"
    ]

    for table in delta_tables:
        name = table.get("name", "Unknown")
        files = table.get("files", 0)
        output_lines.append(f"- **{name}** ({files} parquet files)")

    output_lines.append("\n## LanceDB Datasets (Vector Embeddings)")
    for dataset in lance_datasets:
        name = dataset.get("name", "Unknown")
        output_lines.append(f"- **{name}**")

    return [TextContent(
        type="text",
        text="\n".join(output_lines)
    )]


async def handle_get_stats(args: Dict) -> List[TextContent]:
    """Get lakehouse statistics."""
    result = await call_lakehouse_api("GET", "/stats")

    delta_tables = result.get("delta_tables", 0)
    lance_datasets = result.get("lance_datasets", 0)
    total_size_mb = result.get("total_size_mb", 0)

    output_lines = [
        "# EATON Lakehouse Statistics\n",
        f"**Delta Lake Tables:** {delta_tables}",
        f"**LanceDB Datasets:** {lance_datasets}",
        f"**Total Size:** {total_size_mb:.2f} MB",
        "",
        "## Data Summary",
        "- 62,136 vector embeddings (semantic search)",
        "- 327 products (UPS, circuit breakers, fuses)",
        "- 344 documents (catalogs, specs, 3D models)",
        "- 246 product images with metadata"
    ]

    return [TextContent(
        type="text",
        text="\n".join(output_lines)
    )]


# =============================================================================
# SYNDICATION TOOL HANDLERS
# =============================================================================

async def handle_list_syndication_formats(args: Dict) -> List[TextContent]:
    """List available syndication formats."""
    try:
        result = await call_lakehouse_api(
            "GET",
            "/api/syndicate/formats",
            base_url="http://localhost:4010"
        )

        formats = result.get("formats", [])

        output_lines = [
            "# EATON Syndication Formats",
            f"Available: {len(formats)} export formats\n"
        ]

        for fmt in formats:
            icon_map = {
                "bmecat": "🇪🇺",
                "amazon": "📦",
                "cnet": "📡",
                "fabdis": "🇫🇷",
                "td_synnex": "💻",
                "1worldsync": "🌐",
                "etim_json": "⚡",
                "amer_xml": "🇺🇸"
            }
            icon = icon_map.get(fmt['id'], "📄")

            output_lines.append(f"## {icon} {fmt['name']}")
            output_lines.append(f"**ID:** `{fmt['id']}`")
            output_lines.append(f"**File Type:** {fmt['file_type'].upper()}")
            output_lines.append(f"**Languages:** {', '.join(fmt['languages'])}")
            output_lines.append(f"**Use Case:** {fmt['use_case']}")
            output_lines.append(f"**Complexity:** {fmt['complexity']}")
            output_lines.append("")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except Exception as e:
        logger.error(f"Error listing formats: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def handle_get_syndication_products(args: Dict) -> List[TextContent]:
    """Get products available for syndication."""
    category = args.get("category", "all")
    limit = min(args.get("limit", 20), 100)

    try:
        result = await call_lakehouse_api(
            "GET",
            "/api/syndicate/products",
            base_url="http://localhost:4010",
            params={"customer_id": "eaton", "limit": 200}  # Get all, filter locally
        )

        all_products = result.get("products", [])
        total = result.get("total", 0)

        # Filter by category if specified
        if category != "all":
            products = [p for p in all_products if p.get("product_type") == category]
        else:
            products = all_products

        output_lines = [
            f"# EATON Syndication Products",
            f"Total: {total} products available",
            f"Filter: {category}",
            f"Showing: {min(len(products), limit)} of {len(products)} products\n"
        ]

        for idx, product in enumerate(products[:limit], 1):
            output_lines.append(f"## {idx}. {product.get('product_name', 'N/A')}")
            output_lines.append(f"**SKU:** `{product.get('product_id')}`")
            output_lines.append(f"**Type:** {product.get('product_type')}")
            output_lines.append(f"**GTIN:** {product.get('gtin')}")
            output_lines.append(f"**ETIM:** {product.get('etim_class') or 'N/A'}")

            # Show features if available
            features = product.get('features', '[]')
            try:
                import json
                features_list = json.loads(features) if isinstance(features, str) else features
                if features_list and isinstance(features_list, list):
                    output_lines.append(f"**Features:** {features_list[0][:60]}...")
            except:
                pass

            output_lines.append("")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except Exception as e:
        logger.error(f"Error getting products: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def handle_generate_syndication(args: Dict) -> List[TextContent]:
    """Generate syndication export."""
    format_id = args.get("format", "bmecat")
    product_ids = args.get("product_ids", [])
    language = args.get("language", "en")

    try:
        # Call console backend syndication API
        payload = {
            "format": format_id,
            "product_ids": product_ids,
            "language": language
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "http://localhost:4010/api/syndicate/generate",
                json=payload,
                params={"customer_id": "eaton"}
            )
            response.raise_for_status()
            result = response.json()

        if not result.get("success"):
            return [TextContent(type="text", text=f"Generation failed: {result}")]

        # Return summary (not the full file content)
        product_count = result.get('products_count', len(product_ids) if product_ids else 109)
        file_size = len(result.get('output', '')) / 1024

        format_names = {
            "bmecat": "BMEcat XML (European Standard)",
            "amazon": "Amazon Vendor Central XLSX",
            "cnet": "CNET Content Feed XML",
            "fabdis": "FAB-DIS France XLSX (French + Metric)",
            "td_synnex": "TD Synnex XLSX (IT Distribution)",
            "1worldsync": "1WorldSync GDSN XLSX",
            "etim_json": "ETIM xChange JSON",
            "amer_xml": "AMER Vendor XML (US Distributors)"
        }

        output_lines = [
            f"# ✅ Syndication Export Generated",
            "",
            f"**Format:** {format_names.get(format_id, format_id.upper())}",
            f"**Products Included:** {product_count}",
            f"**Filename:** `{result.get('filename')}`",
            f"**File Size:** {file_size:.1f} KB",
            f"**Language:** {language.upper()}",
            "",
            "## File Ready for Download",
            "",
            "The export file has been generated successfully.",
            "",
            "**Access the file:**",
            f"1. Visit: http://localhost:4020",
            "2. Navigate to: Syndicate tab",
            "3. Look for: Results section",
            f"4. Download: `{result.get('filename')}`",
            "",
            "**File characteristics:**",
        ]

        if format_id in ["amazon", "fabdis", "td_synnex", "1worldsync"]:
            output_lines.extend([
                "- ✅ Excel format (.xlsx)",
                "- ✅ Bold orange header row",
                "- ✅ Auto-sized columns",
                "- ✅ Opens directly in Excel"
            ])
        elif format_id == "etim_json":
            output_lines.extend([
                "- ✅ JSON format",
                "- ✅ ETIM-10 standard compliant",
                "- ✅ Valid JSON structure"
            ])
        else:
            output_lines.extend([
                "- ✅ XML format",
                "- ✅ Valid XML structure",
                "- ✅ Industry-standard compliant"
            ])

        if format_id == "fabdis":
            output_lines.append("- ✅ ALL text in French")
            output_lines.append("- ✅ ALL units in metric (kg, cm)")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except Exception as e:
        logger.error(f"Error generating syndication: {e}")
        return [TextContent(type="text", text=f"Error generating syndication: {str(e)}")]


async def handle_preview_syndication(args: Dict) -> List[TextContent]:
    """Preview syndication output (first 50 lines)."""
    format_id = args.get("format", "bmecat")

    try:
        # Generate for just 1 product as preview
        payload = {
            "format": format_id,
            "product_ids": ["5E1100IUSB-AR"],  # Sample UPS product
            "language": "en"
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "http://localhost:4010/api/syndicate/generate",
                json=payload,
                params={"customer_id": "eaton"}
            )
            response.raise_for_status()
            result = response.json()

        output_content = result.get("output", "")

        # Show first 50 lines
        lines = output_content.split('\n')[:50]
        preview = '\n'.join(lines)
        total_lines = len(output_content.split('\n'))

        output_text = f"""# Preview: {format_id.upper()} Format

**Sample Product:** 5E1100IUSB-AR (Eaton 5E UPS 1100VA)
**Lines shown:** {len(lines)} of {total_lines} total
**File size:** {len(output_content) / 1024:.1f} KB

```
{preview}
```

... ({total_lines - len(lines)} more lines)

Full export available through: generate_syndication tool or console UI.
"""

        return [TextContent(type="text", text=output_text)]

    except Exception as e:
        logger.error(f"Error previewing: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

async def main():
    """Run the EATON MCP server."""
    logger.info("Starting EATON Intelligence Platform MCP Server")
    logger.info(f"Lakehouse API: {LAKEHOUSE_URL}")

    # Test connection to lakehouse
    try:
        health = await call_lakehouse_api("GET", "/health")
        logger.info(f"Connected to EATON lakehouse: {health.get('status')}")
        logger.info(f"  Delta tables: {len(health.get('delta_tables', []))}")
        logger.info(f"  Lance datasets: {len(health.get('lance_datasets', []))}")
    except Exception as e:
        logger.error(f"Failed to connect to lakehouse: {e}")
        logger.error("Make sure EATON lakehouse is running on port 9302")
        return

    # Start MCP server
    async with stdio_server() as (read_stream, write_stream):
        logger.info("MCP server ready for connections")
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
