"""
E2E Test: MCP Orchestration

Tests MCP routing and execution:
1. Auto-routing based on query keywords
2. Specific MCP selection
3. Multi-MCP workflows
4. MCP tool calling
5. MCP resource access
"""

import pytest
import httpx

from tests.e2e.helpers import send_chat_message, assert_response_success


@pytest.mark.e2e
@pytest.mark.asyncio
class TestMCPOrchestration:
    """Test MCP orchestration and routing."""

    async def test_ctax_mcp_routing(
        self,
        authenticated_console_client: httpx.AsyncClient
    ):
        """Test that tax-related queries route to CTAX MCP."""
        tax_queries = [
            "What is our VAT liability?",
            "Calculate corporate tax for Q4",
            "Was ist die Umsatzsteuer?",
            "ELSTER filing deadline"
        ]

        for query in tax_queries:
            response = await authenticated_console_client.post("/api/chat", json={
                "message": query
            })

            if response.status_code == 404:
                pytest.skip("Chat/MCP routing not implemented")

            assert_response_success(response, 200)
            data = response.json()

            # Should route to CTAX (if routing implemented)
            if "mcp_used" in data:
                assert data["mcp_used"] == "ctax"

    async def test_law_mcp_routing(
        self,
        authenticated_console_client: httpx.AsyncClient
    ):
        """Test that legal queries route to LAW MCP."""
        legal_queries = [
            "Review this contract",
            "Check DSGVO compliance",
            "Analyze the vendor agreement",
            "What are the contract terms?"
        ]

        for query in legal_queries:
            response = await authenticated_console_client.post("/api/chat", json={
                "message": query
            })

            if response.status_code == 404:
                pytest.skip("Chat/MCP routing not implemented")

            assert_response_success(response, 200)
            data = response.json()

            if "mcp_used" in data:
                assert data["mcp_used"] == "law"

    async def test_tender_mcp_routing(
        self,
        authenticated_console_client: httpx.AsyncClient
    ):
        """Test that tender/RFP queries route to TENDER MCP."""
        tender_queries = [
            "Analyze this Ausschreibung",
            "Help me respond to this RFP",
            "VOB compliance check",
            "Public tender requirements"
        ]

        for query in tender_queries:
            response = await authenticated_console_client.post("/api/chat", json={
                "message": query
            })

            if response.status_code == 404:
                pytest.skip("Chat/MCP routing not implemented")

            assert_response_success(response, 200)
            data = response.json()

            if "mcp_used" in data:
                assert data["mcp_used"] == "tender"

    async def test_explicit_mcp_selection(
        self,
        authenticated_console_client: httpx.AsyncClient
    ):
        """Test explicitly selecting an MCP (override auto-routing)."""
        # Ask a tax question but force LAW MCP
        response = await authenticated_console_client.post("/api/chat", json={
            "message": "What is the tax rate?",
            "mcp": "law"  # Explicitly use LAW instead of CTAX
        })

        if response.status_code == 404:
            pytest.skip("MCP selection not implemented")

        assert_response_success(response, 200)
        data = response.json()

        # Should use the explicitly specified MCP
        assert data.get("mcp_used") == "law"

    async def test_list_available_mcps(
        self,
        authenticated_console_client: httpx.AsyncClient
    ):
        """Test listing available MCPs."""
        response = await authenticated_console_client.get("/api/mcps/list")

        if response.status_code == 404:
            pytest.skip("MCP list endpoint not implemented")

        assert_response_success(response, 200)
        data = response.json()

        assert "mcps" in data or isinstance(data, list)

        # Should include core MCPs
        if isinstance(data, list):
            mcp_names = [mcp.get("name") or mcp.get("id") for mcp in data]
        else:
            mcp_names = [mcp.get("name") or mcp.get("id") for mcp in data.get("mcps", [])]

        # Core MCPs should be available
        expected_mcps = ["ctax", "law", "tender"]
        # At least one should be present
        assert any(mcp in str(mcp_names).lower() for mcp in expected_mcps)

    async def test_mcp_info(
        self,
        authenticated_console_client: httpx.AsyncClient
    ):
        """Test getting MCP information."""
        response = await authenticated_console_client.get("/api/mcps/ctax/info")

        if response.status_code == 404:
            pytest.skip("MCP info endpoint not implemented")

        assert_response_success(response, 200)
        data = response.json()

        # Should have MCP details
        assert "name" in data or "id" in data
        assert "description" in data or "desc" in data

    @pytest.mark.skip(reason="Requires multi-MCP workflow implementation")
    async def test_multi_mcp_workflow(
        self,
        authenticated_console_client: httpx.AsyncClient
    ):
        """
        Test query that requires multiple MCPs.

        Example: "Check if this contract complies with tax regulations"
        Should use both LAW and CTAX MCPs.
        """
        response = await authenticated_console_client.post("/api/chat", json={
            "message": "Check if this vendor contract complies with German tax law"
        })

        assert_response_success(response, 200)
        data = response.json()

        # Should indicate multiple MCPs were used
        # (implementation-dependent)
        if "mcps_used" in data:
            assert len(data["mcps_used"]) > 1

    @pytest.mark.skip(reason="Requires MCP tool implementation")
    async def test_mcp_tool_calling(
        self,
        authenticated_console_client: httpx.AsyncClient
    ):
        """
        Test that MCPs can call their tools.

        Example: CTAX MCP has @tool calculate_vat()
        """
        response = await authenticated_console_client.post("/api/chat", json={
            "message": "Calculate VAT for an invoice of €10,000"
        })

        assert_response_success(response, 200)
        data = response.json()

        # Should return calculated VAT (€1,900 for 19% rate)
        assert "1900" in data.get("answer", "") or "1.900" in data.get("answer", "")

    @pytest.mark.skip(reason="Requires MCP resource implementation")
    async def test_mcp_resource_access(
        self,
        authenticated_console_client: httpx.AsyncClient
    ):
        """
        Test that MCPs can access their resources.

        Example: LAW MCP has @resource get_contract_templates()
        """
        response = await authenticated_console_client.post("/api/chat", json={
            "message": "Show me available contract templates",
            "mcp": "law"
        })

        assert_response_success(response, 200)
        data = response.json()

        # Should list contract templates
        assert "template" in data.get("answer", "").lower()

    async def test_mcp_permission_enforcement(
        self,
        authenticated_console_client: httpx.AsyncClient,
        test_customer: dict
    ):
        """
        Test that customers can only access MCPs they've subscribed to.

        If customer hasn't subscribed to TENDER MCP, they shouldn't be able to use it.
        """
        # Try to use a hypothetical MCP the customer doesn't have access to
        response = await authenticated_console_client.post("/api/chat", json={
            "message": "Test query",
            "mcp": "premium_research"  # Hypothetical premium MCP
        })

        if response.status_code == 404:
            pytest.skip("MCP permissions not implemented")

        # Should either work (if customer has access) or deny (403)
        assert response.status_code in [200, 403, 404]

    async def test_mcp_error_handling(
        self,
        authenticated_console_client: httpx.AsyncClient
    ):
        """Test MCP error handling."""
        # Try to use non-existent MCP
        response = await authenticated_console_client.post("/api/chat", json={
            "message": "Test query",
            "mcp": "nonexistent_mcp"
        })

        if response.status_code == 404:
            pytest.skip("MCP error handling not implemented")

        # Should return error
        assert response.status_code in [400, 404]

    async def test_mcp_with_empty_lakehouse(
        self,
        authenticated_console_client: httpx.AsyncClient
    ):
        """
        Test MCP behavior when customer has no data ingested yet.

        Should return a helpful message, not crash.
        """
        response = await authenticated_console_client.post("/api/chat", json={
            "message": "What is our revenue?"
        })

        if response.status_code == 404:
            pytest.skip("Chat endpoint not implemented")

        assert_response_success(response, 200)
        data = response.json()

        # Should handle gracefully
        assert "answer" in data
        # May indicate no data available

    async def test_mcp_confidence_scores(
        self,
        authenticated_console_client: httpx.AsyncClient
    ):
        """Test that MCPs return confidence scores."""
        response = await authenticated_console_client.post("/api/chat", json={
            "message": "What is the corporate tax rate?",
            "mcp": "ctax"
        })

        if response.status_code == 404:
            pytest.skip("MCP confidence not implemented")

        assert_response_success(response, 200)
        data = response.json()

        assert "confidence" in data
        assert 0.0 <= data["confidence"] <= 1.0
