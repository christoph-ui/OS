"""
0711 Core MCPs

Official MCPs that ship with the platform.
Always available, no installation required.

Core MCPs:
- CTAX: German tax processing, VAT, compliance
- LAW: Legal document analysis, contracts
- TENDER: RFP/tender processing and response generation
- MARKET: Market intelligence & competitive analysis
- PUBLISH: Multi-channel content publishing
- SYNDICATE: Distribution & syndication
- ORCHESTRATOR: Central platform orchestration (NEW)

Usage:
    from mcps.core import ctax, law, tender, market, publish, syndicate, orchestrator

    # Get MCP instances
    tax_mcp = ctax.CTAXMCP()
    law_mcp = law.LAWMCP()
    tender_mcp = tender.TenderEngineMCP()
    market_mcp = market.MarketMCP()
    publish_mcp = publish.PublishMCP()
    syndicate_mcp = syndicate.SyndicateMCP()
    orchestrator_mcp = orchestrator.OrchestratorMCP()  # NEW
"""

from . import ctax
from . import law
from . import tender
from . import market
from . import publish
from . import syndicate
from . import orchestrator

__all__ = ["ctax", "law", "tender", "market", "publish", "syndicate", "orchestrator"]

# Core MCP identifiers
CORE_MCP_IDS = ["ctax", "law", "tender", "market", "publish", "syndicate", "orchestrator"]
