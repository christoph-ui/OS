"""
0711 Core Platform

The clean, minimal entry point for the 0711 Intelligence Platform.

Usage:
    from zero711 import Platform

    # Initialize platform
    platform = Platform(lakehouse_path="/data/lakehouse")

    # Ingest documents
    platform.ingest("/data/Buchhaltung", mcp="ctax")

    # Query with natural language
    result = await platform.query("What's our Q4 tax liability?")
    print(result.answer)

    # Direct MCP access
    ctax = platform.get_mcp("ctax")
    response = await ctax.process("Calculate VAT for invoice #1234")

Architecture:
    ┌─────────────────────────────────────────────────────────────┐
    │                    0711 CLEAN CORE                          │
    ├─────────────────────────────────────────────────────────────┤
    │                                                             │
    │  from zero711 import Platform                               │
    │  platform.ingest("/data", mcp="ctax")                      │
    │  platform.query("Calculate Q4 taxes")                      │
    │                                                             │
    │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
    │  │ Ingestion   │ │ Lakehouse   │ │ Inference   │          │
    │  └─────────────┘ └─────────────┘ └─────────────┘          │
    │                                                             │
    │  ┌─────────────────────────────────────────────┐          │
    │  │  Core MCPs: CTAX | LAW | TENDER              │          │
    │  └─────────────────────────────────────────────┘          │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘
"""

from .platform import Platform
from .config import PlatformConfig

__version__ = "1.0.0"

__all__ = [
    "Platform",
    "PlatformConfig",
]
