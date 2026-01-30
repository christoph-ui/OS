"""
Pytest Configuration and Fixtures

Provides shared fixtures for all tests.
"""

import pytest
import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for tests."""
    with TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def lakehouse_path(temp_dir):
    """Provide a temporary lakehouse path."""
    path = temp_dir / "lakehouse"
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture
def mock_platform_config(lakehouse_path):
    """Provide mock platform configuration."""
    from core.config import PlatformConfig

    return PlatformConfig(
        lakehouse_path=lakehouse_path,
        vllm_url="http://localhost:8000",
        embedding_url="http://localhost:8001",
        auto_load_core_mcps=False
    )


@pytest.fixture
def mock_mcp_context():
    """Provide mock MCP context."""
    from mcps.sdk import MCPContext

    return MCPContext(
        customer_id="test_customer",
        engagement_id="test_engagement",
        config={}
    )
