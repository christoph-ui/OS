"""
0711 Marketplace MCPs

Optional MCPs that can be installed from the marketplace.
One-click install, usage-based billing.

Marketplace MCPs are downloaded from registry.0711.ai and
installed into the customer's deployment.

Usage:
    from mcps.registry import get_registry

    registry = get_registry()

    # Install from marketplace
    registry.load_from_path("/path/to/downloaded/mcp")

    # Use the MCP
    invoice_mcp = registry.get("invoice-pro")
    result = await invoice_mcp.process(data)
"""

# Marketplace MCPs are dynamically loaded
# This package serves as a namespace for installed MCPs

__all__ = []
