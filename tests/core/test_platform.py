"""
Platform Tests

Tests for the core Platform class.
"""

import pytest
from pathlib import Path


class TestPlatform:
    """Tests for Platform class."""

    def test_platform_init(self, lakehouse_path):
        """Test Platform initialization."""
        from core.platform import Platform

        platform = Platform(lakehouse_path=lakehouse_path)

        assert platform.config.lakehouse_path == lakehouse_path
        assert platform._initialized is False

    def test_platform_config_override(self, lakehouse_path):
        """Test Platform config override."""
        from core.platform import Platform

        custom_vllm = "http://custom-vllm:9000"
        platform = Platform(
            lakehouse_path=lakehouse_path,
            vllm_url=custom_vllm
        )

        assert platform.config.vllm_url == custom_vllm

    def test_query_result_dataclass(self):
        """Test QueryResult dataclass."""
        from core.platform import QueryResult

        result = QueryResult(
            answer="Test answer",
            confidence=0.95,
            mcp_used="ctax",
            sources=["doc1.pdf", "doc2.pdf"],
            metadata={"key": "value"}
        )

        assert result.answer == "Test answer"
        assert result.confidence == 0.95
        assert result.mcp_used == "ctax"
        assert len(result.sources) == 2


class TestQueryRouting:
    """Tests for query routing."""

    @pytest.mark.asyncio
    async def test_route_tax_query(self, lakehouse_path):
        """Test routing of tax-related queries."""
        from core.platform import Platform

        platform = Platform(lakehouse_path=lakehouse_path)

        # Test German tax keywords
        assert await platform._route_query("Was ist unsere Umsatzsteuer?") == "ctax"
        assert await platform._route_query("Calculate VAT for invoice") == "ctax"
        assert await platform._route_query("ELSTER Anmeldung") == "ctax"

    @pytest.mark.asyncio
    async def test_route_legal_query(self, lakehouse_path):
        """Test routing of legal queries."""
        from core.platform import Platform

        platform = Platform(lakehouse_path=lakehouse_path)

        # Test legal keywords
        assert await platform._route_query("Vertrag prüfen") == "law"
        assert await platform._route_query("Contract compliance check") == "law"
        assert await platform._route_query("DSGVO requirements") == "law"

    @pytest.mark.asyncio
    async def test_route_tender_query(self, lakehouse_path):
        """Test routing of tender queries."""
        from core.platform import Platform

        platform = Platform(lakehouse_path=lakehouse_path)

        # Test tender keywords
        assert await platform._route_query("Ausschreibung analysieren") == "tender"
        assert await platform._route_query("RFP response") == "tender"
        assert await platform._route_query("VOB compliance") == "tender"

    @pytest.mark.asyncio
    async def test_route_default_to_ctax(self, lakehouse_path):
        """Test default routing when no keywords match."""
        from core.platform import Platform

        platform = Platform(lakehouse_path=lakehouse_path)

        # Should default to ctax
        assert await platform._route_query("generic question") == "ctax"
