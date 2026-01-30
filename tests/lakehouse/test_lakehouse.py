"""
Lakehouse Tests

Tests for the Lakehouse class.
"""

import pytest
from pathlib import Path


class TestLakehouse:
    """Tests for Lakehouse class."""

    def test_lakehouse_init(self, temp_dir):
        """Test Lakehouse initialization."""
        from lakehouse import Lakehouse

        lh = Lakehouse(temp_dir / "lakehouse")

        assert lh.path.exists()
        assert lh.delta_path == lh.path / "delta"
        assert lh.lance_path == lh.path / "lance"

    def test_lakehouse_creates_directories(self, temp_dir):
        """Test Lakehouse creates necessary directories."""
        from lakehouse import Lakehouse

        path = temp_dir / "new_lakehouse"
        assert not path.exists()

        lh = Lakehouse(path)

        assert path.exists()

    def test_extract_mcp_from_query(self, lakehouse_path):
        """Test MCP extraction from SQL queries."""
        from lakehouse import Lakehouse

        lh = Lakehouse(lakehouse_path)

        # Test FROM table pattern
        assert lh._extract_mcp_from_query("SELECT * FROM ctax_documents") == "ctax"
        assert lh._extract_mcp_from_query("SELECT * FROM law_chunks") == "law"

        # Test mcp = 'value' pattern
        assert lh._extract_mcp_from_query("SELECT * FROM docs WHERE mcp = 'tender'") == "tender"

        # Test category pattern
        assert lh._extract_mcp_from_query("SELECT * FROM docs WHERE category = 'tax'") == "tax"

    def test_lakehouse_repr(self, lakehouse_path):
        """Test Lakehouse string representation."""
        from lakehouse import Lakehouse

        lh = Lakehouse(lakehouse_path)

        assert str(lakehouse_path) in repr(lh)
        assert "Lakehouse" in repr(lh)


class TestLakehouseStats:
    """Tests for Lakehouse statistics."""

    def test_get_statistics(self, lakehouse_path):
        """Test getting lakehouse statistics."""
        from lakehouse import Lakehouse

        lh = Lakehouse(lakehouse_path)
        stats = lh.get_statistics()

        assert "path" in stats
        assert "delta" in stats
        assert "lance" in stats

    def test_list_mcps_empty(self, lakehouse_path):
        """Test listing MCPs when empty."""
        from lakehouse import Lakehouse

        lh = Lakehouse(lakehouse_path)
        mcps = lh.list_mcps()

        assert isinstance(mcps, list)
