"""
Integration Tests for Orchestrator MCP

Tests full workflow with real services (requires services to be running)
"""
import pytest
import httpx
import os
from pathlib import Path

# Check if services are available
CRADLE_AVAILABLE = os.getenv("CRADLE_AVAILABLE", "false") == "true"
MCP_CENTRAL_AVAILABLE = os.getenv("MCP_CENTRAL_AVAILABLE", "false") == "true"

requires_cradle = pytest.mark.skipif(
    not CRADLE_AVAILABLE,
    reason="Cradle services not available"
)

requires_mcp_central = pytest.mark.skipif(
    not MCP_CENTRAL_AVAILABLE,
    reason="MCP Central not available"
)


class TestCradleIntegration:
    """Test integration with Cradle services"""

    @requires_cradle
    @pytest.mark.asyncio
    async def test_cradle_embedding_service(self):
        """Test Cradle embedding service"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8001/embed",
                json={"texts": ["Test document"]}
            )

            assert response.status_code == 200
            data = response.json()
            assert "embeddings" in data
            assert len(data["embeddings"]) == 1

    @requires_cradle
    @pytest.mark.asyncio
    async def test_cradle_vision_service(self):
        """Test Cradle vision service"""
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8002/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"


class TestMCPCentralIntegration:
    """Test integration with MCP Central"""

    @requires_mcp_central
    @pytest.mark.asyncio
    async def test_mcp_central_health(self):
        """Test MCP Central health"""
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:4090/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"

    @requires_mcp_central
    @pytest.mark.asyncio
    async def test_mcp_central_embeddings(self):
        """Test MCP Central embeddings endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:4090/api/embeddings/generate",
                json={
                    "texts": ["Test text for embedding"],
                    "customer_id": "test"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["embeddings"]) == 1


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows"""

    @pytest.mark.asyncio
    async def test_orchestrator_api_health(self):
        """Test orchestrator API is accessible"""
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:4080/health")

            assert response.status_code == 200

    @pytest.mark.skip(reason="Requires full deployment")
    @pytest.mark.asyncio
    async def test_complete_customer_onboarding(self):
        """
        Test complete customer onboarding workflow

        This test would:
        1. Initialize customer via Orchestrator API
        2. Wait for processing
        3. Verify deployment
        4. Test data access
        5. Cleanup
        """
        pass


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
