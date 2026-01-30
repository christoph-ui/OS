"""
Mock MCPs for Testing

Mock implementations of core MCPs that return canned responses.
"""

from typing import Dict, Any, Optional


class BaseMockMCP:
    """Base class for mock MCPs."""

    def __init__(self):
        self.name = "mock"
        self.description = "Mock MCP for testing"
        self.context = None

    def set_context(self, context):
        """Set execution context."""
        self.context = context

    async def process(self, query: str, context: Optional[Dict] = None):
        """Process query and return mock response."""
        raise NotImplementedError


class MockCTaxMCP(BaseMockMCP):
    """Mock CTAX MCP for tax-related queries."""

    def __init__(self):
        super().__init__()
        self.name = "ctax"
        self.description = "German tax automation specialist (MOCK)"

    async def process(self, query: str, context: Optional[Dict] = None):
        """Return mock tax response."""
        from .mock_responses import MOCK_VLLM_RESPONSES

        class MockResponse:
            def __init__(self, data, confidence, metadata=None):
                self.data = data
                self.confidence = confidence
                self.metadata = metadata or {}

        response_data = MOCK_VLLM_RESPONSES["tax_query"]

        return MockResponse(
            data={
                "answer": response_data["answer"],
                "sources": response_data["sources"],
                "analysis": "Mock tax analysis"
            },
            confidence=response_data["confidence"],
            metadata={"mcp": "ctax", "mock": True}
        )


class MockLawMCP(BaseMockMCP):
    """Mock LAW MCP for legal queries."""

    def __init__(self):
        super().__init__()
        self.name = "law"
        self.description = "Legal document analysis specialist (MOCK)"

    async def process(self, query: str, context: Optional[Dict] = None):
        """Return mock legal response."""
        from .mock_responses import MOCK_VLLM_RESPONSES

        class MockResponse:
            def __init__(self, data, confidence, metadata=None):
                self.data = data
                self.confidence = confidence
                self.metadata = metadata or {}

        response_data = MOCK_VLLM_RESPONSES["legal_query"]

        return MockResponse(
            data={
                "answer": response_data["answer"],
                "sources": response_data["sources"],
                "analysis": "Mock legal analysis"
            },
            confidence=response_data["confidence"],
            metadata={"mcp": "law", "mock": True}
        )


class MockTenderMCP(BaseMockMCP):
    """Mock TENDER MCP for tender/RFP queries."""

    def __init__(self):
        super().__init__()
        self.name = "tender"
        self.description = "Public tender analysis specialist (MOCK)"

    async def process(self, query: str, context: Optional[Dict] = None):
        """Return mock tender response."""
        from .mock_responses import MOCK_VLLM_RESPONSES

        class MockResponse:
            def __init__(self, data, confidence, metadata=None):
                self.data = data
                self.confidence = confidence
                self.metadata = metadata or {}

        response_data = MOCK_VLLM_RESPONSES["tender_query"]

        return MockResponse(
            data={
                "answer": response_data["answer"],
                "sources": response_data["sources"],
                "analysis": "Mock tender analysis"
            },
            confidence=response_data["confidence"],
            metadata={"mcp": "tender", "mock": True}
        )
