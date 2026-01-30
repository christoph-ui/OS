"""
0711 Intelligence Platform

Clean, minimal interface for enterprise AI.

Usage:
    from zero711 import Platform

    platform = Platform()
    platform.ingest("/data/Buchhaltung", mcp="ctax")
    result = await platform.query("What's our Q4 tax liability?")

Components:
    - Platform: Main entry point
    - MCPs: AI solutions (CTAX, LAW, TENDER)
    - Lakehouse: Data storage (Delta Lake + Lance)
    - Inference: Model serving (Mixtral + LoRA)

Philosophy:
    Like Ray - keep the core clean and minimal.
    Let the ecosystem grow on top.
"""

# Main entry point
from core import Platform, PlatformConfig

# MCP access
from mcps import get_mcp, get_registry, BaseMCP

__version__ = "1.0.0"

__all__ = [
    "Platform",
    "PlatformConfig",
    "get_mcp",
    "get_registry",
    "BaseMCP",
]

# Quick start
def quickstart():
    """Print quickstart guide"""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                    0711 Intelligence Platform                  ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║  Quick Start:                                                  ║
║                                                               ║
║    from zero711 import Platform                               ║
║                                                               ║
║    platform = Platform()                                      ║
║    platform.ingest("/data/docs", mcp="ctax")                 ║
║    result = await platform.query("Calculate Q4 taxes")       ║
║                                                               ║
║  Core MCPs:                                                    ║
║    • ctax  - German tax processing                            ║
║    • law   - Legal document analysis                          ║
║    • tender - RFP/tender processing                          ║
║                                                               ║
║  Docs: https://docs.0711.io                                   ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
""")
