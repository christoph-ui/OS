"""
Unit Tests for Orchestrator MCP

Tests core orchestrator functionality without external dependencies
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path

from mcps.core.orchestrator import OrchestratorMCP


@pytest.fixture
def orchestrator():
    """Create orchestrator instance"""
    return OrchestratorMCP()


@pytest.fixture
def mock_user():
    """Mock user"""
    return {
        "user_id": "test-user-id",
        "customer_id": "test-customer",
        "email": "test@example.com",
        "role": "customer_admin"
    }


class TestOrchestratorInit:
    """Test orchestrator initialization"""

    def test_initialization(self, orchestrator):
        """Test that orchestrator initializes correctly"""
        assert orchestrator.metadata.id == "orchestrator"
        assert orchestrator.metadata.name == "0711 Orchestrator"
        assert orchestrator.metadata.version == "1.0.0"

    def test_lazy_loading(self, orchestrator):
        """Test that services are lazy loaded"""
        assert orchestrator._user_registry is None
        assert orchestrator._db_gateway is None
        assert orchestrator._marketplace is None


class TestCustomerInitialization:
    """Test customer initialization"""

    @pytest.mark.asyncio
    @patch('orchestrator.auth.user_registry.UserRegistry')
    @patch('orchestrator.cradle.cradle_client.CradleClient')
    async def test_initialize_customer_success(
        self,
        mock_cradle,
        mock_registry,
        orchestrator
    ):
        """Test successful customer initialization"""

        # Mock user registry
        mock_registry_instance = AsyncMock()
        mock_registry_instance.create_user = AsyncMock(return_value={
            "id": "user-123",
            "customer_id": "test-customer",
            "email": "admin@test.com",
            "token": "test-token"
        })
        mock_registry.return_value = mock_registry_instance

        # Mock cradle client
        mock_cradle_instance = AsyncMock()
        mock_cradle_instance.upload_to_staging = AsyncMock(
            return_value=Path("/staging/test-customer")
        )
        mock_cradle_instance.process_customer_data = AsyncMock(return_value={
            "stats": {
                "total_files": 100,
                "total_documents": 5000
            },
            "output_path": Path("/staging/test-customer/processed")
        })
        mock_cradle.return_value = mock_cradle_instance

        # Test initialization
        result = await orchestrator.initialize_customer(
            company_name="Test Company",
            contact_email="admin@test.com",
            data_sources=["/data/test"],
            deployment_target="on-premise"
        )

        assert result["success"] is True
        assert result["customer_id"] == "test-company"
        assert "user_id" in result
        assert "user_token" in result


class TestIncrementalUpdates:
    """Test incremental update functionality"""

    @pytest.mark.asyncio
    @patch('orchestrator.auth.user_registry.UserRegistry')
    async def test_process_new_documents(
        self,
        mock_registry,
        orchestrator,
        mock_user
    ):
        """Test processing new documents"""

        # Mock user registry
        mock_registry_instance = AsyncMock()
        mock_registry_instance.verify_token = AsyncMock(return_value=mock_user)
        mock_registry.return_value = mock_registry_instance

        # Mock embedding generation
        with patch.object(
            orchestrator,
            '_generate_embeddings_via_central',
            AsyncMock(return_value=[[0.1, 0.2, 0.3]])
        ):
            result = await orchestrator.process_new_documents(
                customer_id="test-customer",
                user_token="test-token",
                file_paths=["/data/test.pdf"]
            )

            assert result["success"] is True
            assert result["processed_files"] == 1


class TestDatabaseAccess:
    """Test database access functionality"""

    @pytest.mark.asyncio
    @patch('orchestrator.database_gateway.SecureDatabaseGateway')
    async def test_query_customer_database(
        self,
        mock_gateway,
        orchestrator
    ):
        """Test database query with authorization"""

        # Mock database gateway
        mock_gateway_instance = AsyncMock()
        mock_gateway_instance.execute_query = AsyncMock(return_value={
            "success": True,
            "results": []
        })
        mock_gateway.return_value = mock_gateway_instance

        result = await orchestrator.query_customer_database(
            customer_id="test-customer",
            user_token="test-token",
            database="lakehouse",
            query="SELECT * FROM documents LIMIT 10",
            require_approval=False
        )

        assert result["success"] is True


class TestMarketplace:
    """Test marketplace functionality"""

    @pytest.mark.asyncio
    @patch('orchestrator.marketplace.marketplace_gateway.MarketplaceGateway')
    async def test_list_marketplace_mcps(
        self,
        mock_marketplace,
        orchestrator
    ):
        """Test listing marketplace MCPs"""

        # Mock marketplace
        mock_marketplace_instance = AsyncMock()
        mock_marketplace_instance.list_mcps = AsyncMock(return_value={
            "success": True,
            "total": 3,
            "mcps": [
                {"name": "ctax", "installed": True},
                {"name": "law", "installed": False},
                {"name": "etim", "installed": True}
            ]
        })
        mock_marketplace.return_value = mock_marketplace_instance

        result = await orchestrator.list_marketplace_mcps(
            user_token="test-token"
        )

        assert result["success"] is True
        assert result["total"] == 3

    @pytest.mark.asyncio
    @patch('orchestrator.marketplace.marketplace_gateway.MarketplaceGateway')
    async def test_install_mcp(
        self,
        mock_marketplace,
        orchestrator
    ):
        """Test MCP installation"""

        # Mock marketplace
        mock_marketplace_instance = AsyncMock()
        mock_marketplace_instance.install_mcp = AsyncMock(return_value={
            "success": True,
            "installation_id": "inst-123",
            "mcp_name": "etim",
            "license_key": "0711-ABCD1234"
        })
        mock_marketplace.return_value = mock_marketplace_instance

        result = await orchestrator.install_mcp(
            user_token="test-token",
            mcp_name="etim"
        )

        assert result["success"] is True
        assert result["mcp_name"] == "etim"


class TestIntelligence:
    """Test intelligence layer"""

    @pytest.mark.asyncio
    @patch('orchestrator.intelligence.change_detector.DataChangeDetector')
    async def test_get_data_changes(
        self,
        mock_detector,
        orchestrator
    ):
        """Test change detection"""

        # Mock change detector
        mock_detector_instance = AsyncMock()
        mock_detector_instance.detect_changes = AsyncMock(return_value={
            "success": True,
            "changes": {
                "new_documents": 500,
                "new_images": 100
            },
            "service_offers": [
                {"service_type": "embeddings", "estimated_cost_eur": 5.0}
            ]
        })
        mock_detector.return_value = mock_detector_instance

        result = await orchestrator.get_data_changes(
            customer_id="test-customer",
            user_token="test-token"
        )

        assert result["success"] is True
        assert result["changes"]["new_documents"] == 500


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
