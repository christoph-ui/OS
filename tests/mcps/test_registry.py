"""
MCP Registry Tests

Tests for the MCP registry system.
"""

import pytest


class TestMCPRegistry:
    """Tests for MCPRegistry class."""

    def test_registry_singleton(self):
        """Test registry returns singleton."""
        from mcps.registry import get_registry

        reg1 = get_registry()
        reg2 = get_registry()

        assert reg1 is reg2

    def test_list_core_mcps(self):
        """Test listing core MCPs."""
        from mcps.registry import get_registry, CORE_MCPS

        registry = get_registry()
        core = registry.list_core()

        assert core == CORE_MCPS
        assert "ctax" in core
        assert "law" in core
        assert "tender" in core

    def test_is_core_mcp(self):
        """Test checking if MCP is core."""
        from mcps.registry import get_registry

        registry = get_registry()

        assert registry.is_core("ctax") is True
        assert registry.is_core("law") is True
        assert registry.is_core("tender") is True
        assert registry.is_core("custom_mcp") is False

    def test_register_mcp(self):
        """Test MCP registration."""
        from mcps.registry import MCPRegistry
        from mcps.sdk import BaseMCP, MCPResponse

        # Create a test MCP
        class TestMCP(BaseMCP):
            name = "test_mcp"
            version = "1.0.0"

            async def process(self, input, context=None):
                return MCPResponse(data={"test": True})

        registry = MCPRegistry()
        test_mcp = TestMCP()
        registry.register(test_mcp)

        assert registry.is_registered("test_mcp")
        assert registry.get("test_mcp") is test_mcp


class TestMCPBase:
    """Tests for BaseMCP class."""

    def test_mcp_requires_name(self):
        """Test that MCP requires name."""
        from mcps.sdk import BaseMCP

        with pytest.raises(ValueError, match="must define 'name'"):
            class InvalidMCP(BaseMCP):
                version = "1.0.0"

                async def process(self, input, context=None):
                    pass

            InvalidMCP()

    def test_mcp_requires_version(self):
        """Test that MCP requires version."""
        from mcps.sdk import BaseMCP

        with pytest.raises(ValueError, match="must define 'version'"):
            class InvalidMCP(BaseMCP):
                name = "test"

                async def process(self, input, context=None):
                    pass

            InvalidMCP()

    def test_mcp_info_property(self):
        """Test MCP info property."""
        from mcps.sdk import BaseMCP, MCPResponse

        class TestMCP(BaseMCP):
            name = "info_test"
            version = "2.0.0"
            description = "Test MCP"
            category = "test"
            lora_adapter = "adapters/test"

            async def process(self, input, context=None):
                return MCPResponse(data={})

        mcp = TestMCP()
        info = mcp.info

        assert info["name"] == "info_test"
        assert info["version"] == "2.0.0"
        assert info["description"] == "Test MCP"
        assert info["category"] == "test"
        assert info["lora_adapter"] == "adapters/test"
