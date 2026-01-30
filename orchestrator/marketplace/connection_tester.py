"""
Connection Tester

Tests MCP connections before activation
"""
import logging
from typing import Dict, Optional
import httpx
import asyncio

logger = logging.getLogger(__name__)


class ConnectionTester:
    """Tests MCP connections"""

    async def test_mcp_connection(
        self,
        mcp_name: str,
        connection_type: str,
        direction: str,
        config: Optional[Dict] = None
    ) -> Dict:
        """
        Test MCP connection

        Args:
            mcp_name: MCP name
            connection_type: 'shared', 'sidecar', 'api'
            direction: 'input' or 'output'
            config: Connection configuration

        Returns:
            Test results
        """
        logger.info(f"Testing {mcp_name} connection ({direction})")

        if connection_type == "shared":
            return await self._test_shared_connection(mcp_name)
        elif connection_type == "sidecar":
            return await self._test_sidecar_connection(mcp_name, config)
        elif connection_type == "api":
            return await self._test_api_connection(mcp_name, config)
        else:
            return {
                "status": "error",
                "message": f"Unknown connection type: {connection_type}"
            }

    async def _test_shared_connection(self, mcp_name: str) -> Dict:
        """Test connection to shared MCP service"""

        # Map MCP to port
        mcp_ports = {
            "etim": 7779,
            "market": 7780,
            "publish": 7781
        }

        port = mcp_ports.get(mcp_name)
        if not port:
            return {
                "status": "error",
                "message": f"Unknown shared MCP: {mcp_name}"
            }

        # Test connection
        url = f"http://localhost:{port}/health"

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                start_time = asyncio.get_event_loop().time()
                response = await client.get(url)
                latency_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)

                if response.status_code == 200:
                    return {
                        "status": "ok",
                        "latency_ms": latency_ms,
                        "message": f"Connected to {mcp_name} service",
                        "url": url
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Service returned {response.status_code}",
                        "url": url
                    }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Connection failed: {str(e)}",
                "url": url
            }

    async def _test_sidecar_connection(
        self,
        mcp_name: str,
        config: Optional[Dict]
    ) -> Dict:
        """Test connection to sidecar MCP"""

        # Sidecar URL format: http://{customer_id}-{mcp_name}:8000
        # Would need customer_id from config
        customer_id = config.get("customer_id") if config else "unknown"
        url = f"http://{customer_id}-{mcp_name}:8000/health"

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)

                if response.status_code == 200:
                    return {
                        "status": "ok",
                        "message": f"Sidecar container responding",
                        "url": url
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Service returned {response.status_code}"
                    }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Sidecar not accessible: {str(e)}"
            }

    async def _test_api_connection(
        self,
        mcp_name: str,
        config: Optional[Dict]
    ) -> Dict:
        """Test connection to external API"""

        if not config or "api_url" not in config:
            return {
                "status": "error",
                "message": "API URL not provided in config"
            }

        url = config["api_url"]

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Test endpoint
                response = await client.get(f"{url}/health")

                if response.status_code == 200:
                    return {
                        "status": "ok",
                        "message": "External API responding",
                        "url": url
                    }
                else:
                    return {
                        "status": "warning",
                        "message": f"API returned {response.status_code} (might still work)"
                    }

        except Exception as e:
            return {
                "status": "error",
                "message": f"API connection failed: {str(e)}"
            }
