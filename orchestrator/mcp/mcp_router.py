"""
MCP Router - Routes customer queries to shared MCP services

Provides customer-isolated access to shared MCP services without deploying
per-customer MCP containers.
"""

import logging
from typing import Dict, Optional, Any
from dataclasses import dataclass
import httpx
from pathlib import Path
from core.paths import CustomerPaths

logger = logging.getLogger(__name__)


@dataclass
class MCPConfig:
    """Configuration for a shared MCP service"""
    name: str
    url: str
    type: str  # "shared" or "per-customer"
    description: str
    capabilities: list[str]
    version: str = "1.0"
    provider_path: Optional[Path] = None


class MCPRouter:
    """
    Routes customer queries to appropriate shared MCP services.

    Ensures data isolation by adding customer context to all requests.
    """

    def __init__(self):
        self.mcps: Dict[str, MCPConfig] = {}
        self._load_mcp_registry()

    def _load_mcp_registry(self):
        """Load available shared MCPs"""
        # ETIM MCP (shared service)
        self.mcps["etim"] = MCPConfig(
            name="etim",
            url="http://localhost:7779/api/quality",  # Actual ETIM API endpoint
            type="shared",
            description="ETIM/ECLASS product classification and semantic search",
            capabilities=[
                "product_classification",
                "semantic_search",
                "etim_mapping",
                "eclass_mapping",
                "feature_extraction"
            ],
            version="2.0",
            provider_path=Path("/home/christoph.bertsch/0711/0711-etim-mcp")
        )

        # MARKET MCP (NEW) - Market Intelligence
        self.mcps["market"] = MCPConfig(
            name="market",
            url="http://localhost:7780/market",  # Dedicated port for MARKET MCP
            type="shared",
            description="Market Intelligence & Competitive Analysis Engine",
            capabilities=[
                "competitive_analysis",
                "pricing_intelligence",
                "market_coverage",
                "web_search_integration",
                "opportunity_detection"
            ],
            version="1.0",
            provider_path=Path("/home/christoph.bertsch/0711/mcps/market")
        )

        # PUBLISH MCP (NEW) - Content Publishing
        self.mcps["publish"] = MCPConfig(
            name="publish",
            url="http://localhost:7781/publish",  # Dedicated port for PUBLISH MCP
            type="shared",
            description="Multi-Channel Content Publishing Engine",
            capabilities=[
                "ecommerce_optimization",
                "datasheet_generation",
                "marketing_content",
                "distributor_feeds",
                "seo_optimization",
                "content_pack_generation"
            ],
            version="1.0",
            provider_path=Path("/home/christoph.bertsch/0711/mcps/publish")
        )

        logger.info(f"Loaded {len(self.mcps)} shared MCPs (ETIM, MARKET, PUBLISH)")

    async def query_mcp(
        self,
        mcp_name: str,
        customer_id: str,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Route query to shared MCP with customer context.

        Args:
            mcp_name: Name of MCP (e.g., "etim")
            customer_id: Customer ID for isolation
            query: Query text
            context: Optional context (lakehouse path, filters, etc.)
            timeout: Request timeout in seconds

        Returns:
            MCP response with results

        Raises:
            ValueError: If MCP not found or not enabled for customer
            httpx.HTTPError: If MCP request fails
        """
        # Validate MCP exists
        if mcp_name not in self.mcps:
            raise ValueError(f"MCP '{mcp_name}' not found in registry")

        mcp = self.mcps[mcp_name]

        # Build request with customer context (format varies by MCP)
        if mcp_name == "etim":
            # ETIM expects catalogData array format
            request_data = {
                "catalogData": [{
                    "productId": "query",
                    "description": query,
                    "customer_id": customer_id,
                    "context": context or {}
                }]
            }
        else:
            # Standard format for other MCPs
            request_data = {
                "query": query,
                "customer_id": customer_id,
                "context": context or {}
            }

        # Add lakehouse path for data access (persistent storage)
        if mcp_name != "etim":  # Standard MCPs use context field
            if "lakehouse_path" not in request_data.get("context", {}):
                lakehouse_path = str(CustomerPaths.get_lakehouse_path(customer_id))
                request_data["context"]["lakehouse_path"] = lakehouse_path
                logger.debug(f"Added lakehouse path: {lakehouse_path}")

        headers = {
            "X-Customer-ID": customer_id,
            "Content-Type": "application/json"
        }

        # Determine endpoint based on MCP type
        if mcp_name == "etim":
            endpoint = f"{mcp.url}/analyze"  # ETIM uses /api/quality/analyze
        else:
            endpoint = f"{mcp.url}/query"  # Default endpoint

        logger.info(f"Routing query to {mcp_name} MCP for customer {customer_id} at {endpoint}")

        # Send request to shared MCP
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                response = await client.post(
                    endpoint,
                    json=request_data,
                    headers=headers
                )
                response.raise_for_status()

                result = response.json()
                logger.info(f"MCP {mcp_name} returned {len(result.get('results', []))} results")

                return result

            except httpx.HTTPError as e:
                logger.error(f"MCP request failed: {e}")
                raise

    async def check_mcp_health(self, mcp_name: str) -> bool:
        """
        Check if MCP service is healthy.

        Args:
            mcp_name: Name of MCP to check

        Returns:
            True if MCP is healthy, False otherwise
        """
        if mcp_name not in self.mcps:
            return False

        mcp = self.mcps[mcp_name]

        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{mcp.url}/health")
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"MCP {mcp_name} health check failed: {e}")
            return False

    def list_mcps(self) -> list[Dict[str, Any]]:
        """
        List all available shared MCPs.

        Returns:
            List of MCP info dicts
        """
        return [
            {
                "name": mcp.name,
                "url": mcp.url,
                "type": mcp.type,
                "description": mcp.description,
                "capabilities": mcp.capabilities,
                "version": mcp.version
            }
            for mcp in self.mcps.values()
        ]

    def get_mcp_info(self, mcp_name: str) -> Optional[Dict[str, Any]]:
        """
        Get info about a specific MCP.

        Args:
            mcp_name: Name of MCP

        Returns:
            MCP info dict or None if not found
        """
        mcp = self.mcps.get(mcp_name)
        if not mcp:
            return None

        return {
            "name": mcp.name,
            "url": mcp.url,
            "type": mcp.type,
            "description": mcp.description,
            "capabilities": mcp.capabilities,
            "version": mcp.version,
            "provider_path": str(mcp.provider_path) if mcp.provider_path else None
        }


# Global MCP router instance
mcp_router = MCPRouter()
