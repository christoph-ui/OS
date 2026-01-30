"""
0711 MCP SDK
Framework for building Model Context Protocols (MCPs)

Clean, minimal interface for building AI solutions.

Example:
    from mcps.sdk import BaseMCP, MCPContext, MCPResponse

    class MyMCP(BaseMCP):
        name = "my-mcp"
        version = "1.0.0"
        lora_adapter = "adapters/my-lora"

        async def process(self, input, context=None):
            result = await self.generate(f"Process: {input}")
            return MCPResponse(data=result, confidence=0.95)
"""

# New simplified interface (preferred)
from .base import BaseMCP, MCPContext, MCPResponse

# Legacy types (for backwards compatibility)
from .types import ModelSpec, ModelType, MCPMetadata, TaskInput, TaskOutput, UsageMetrics

# Decorators
from .decorators import mcp_endpoint, requires_model, track_usage

# Legacy base class (deprecated - use base.BaseMCP)
from .base_mcp import BaseMCP as LegacyBaseMCP

__version__ = "2.0.0"

__all__ = [
    # New simplified interface
    "BaseMCP",
    "MCPContext",
    "MCPResponse",
    # Legacy types (backwards compatibility)
    "ModelSpec",
    "ModelType",
    "MCPMetadata",
    "TaskInput",
    "TaskOutput",
    "UsageMetrics",
    "LegacyBaseMCP",
    # Decorators
    "mcp_endpoint",
    "requires_model",
    "track_usage",
]
