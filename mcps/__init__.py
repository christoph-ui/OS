"""
0711 MCPs Package

Model Context Protocols (MCPs) - AI solutions for specific business domains.

Architecture:
    mcps/
    ├── sdk/           # SDK for building MCPs
    │   └── base.py    # BaseMCP class
    ├── registry.py    # Central MCP registry
    ├── core/          # Core MCPs (ship with platform)
    │   ├── ctax.py    # German Tax
    │   ├── law.py     # Legal/Contracts
    │   └── tender.py  # RFP Processing
    └── marketplace/   # Optional MCPs (one-click install)

Usage:
    from mcps.registry import get_registry, get_mcp
    from mcps.sdk import BaseMCP

    # Get an MCP
    ctax = get_mcp("ctax")

    # List core MCPs
    registry = get_registry()
    print(registry.list_core())  # ["ctax", "law", "tender"]
"""

from .registry import MCPRegistry, get_registry, get_mcp, register_mcp
from .sdk import BaseMCP, MCPContext, MCPResponse

__version__ = "2.0.0"

__all__ = [
    "MCPRegistry",
    "get_registry",
    "get_mcp",
    "register_mcp",
    "BaseMCP",
    "MCPContext",
    "MCPResponse",
]
