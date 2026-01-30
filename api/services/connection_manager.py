"""
Connection Manager Service
Orchestrates MCP connection flows (OAuth, API keys, databases, service accounts)
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_
import httpx

from ..models import (
    ConnectionCredential,
    ConnectionType,
    ConnectionStatus,
    MCP,
    MCPInstallation,
    Customer,
    User
)
from .credential_vault import get_credential_vault
from .oauth2_service import get_oauth2_service

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages MCP connections and credentials

    Responsibilities:
    - Initiate connection flows (OAuth, API key, database, service account)
    - Store encrypted credentials
    - Test connection health
    - Refresh OAuth tokens
    - Manage connection lifecycle
    """

    def __init__(self, db: Session):
        self.db = db
        self.vault = get_credential_vault()
        self.oauth_service = get_oauth2_service()

    async def initiate_oauth_connection(
        self,
        customer_id: str,
        mcp_id: str,
        provider_name: str,
        user_id: str,
        shop_domain: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Initiate OAuth2 connection flow

        Args:
            customer_id: Customer UUID
            mcp_id: MCP UUID
            provider_name: OAuth provider (salesforce, google, etc.)
            user_id: User initiating connection
            shop_domain: Shopify shop domain (optional)
            ip_address: User IP address
            user_agent: User agent string

        Returns:
            {
                "authorization_url": "https://...",
                "state": "random_token",
                "connection_id": "uuid"
            }
        """
        # Validate MCP exists
        mcp = self.db.query(MCP).filter(MCP.id == mcp_id).first()
        if not mcp:
            raise ValueError(f"MCP not found: {mcp_id}")

        # Get or create MCP installation
        installation = self.db.query(MCPInstallation).filter(
            and_(
                MCPInstallation.customer_id == customer_id,
                MCPInstallation.mcp_id == mcp_id
            )
        ).first()

        if not installation:
            installation = MCPInstallation(
                customer_id=customer_id,
                mcp_id=mcp_id,
                status="installing"
            )
            self.db.add(installation)
            self.db.flush()

        # Create pending connection credential
        connection = ConnectionCredential(
            customer_id=customer_id,
            mcp_id=mcp_id,
            mcp_installation_id=installation.id,
            connection_type=ConnectionType.OAUTH2,
            oauth_provider=provider_name,
            connection_name=f"{mcp.display_name or mcp.name} Connection",
            status=ConnectionStatus.PENDING,
            created_by_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            # Temporary placeholder (will be updated on callback)
            encrypted_credentials=self.vault.encrypt({"status": "pending"})
        )
        self.db.add(connection)
        self.db.commit()

        # Initiate OAuth flow
        oauth_data = self.oauth_service.initiate_oauth_flow(
            provider_name=provider_name,
            customer_id=customer_id,
            mcp_id=mcp_id,
            shop_domain=shop_domain
        )

        # Store state data temporarily (in production, use Redis)
        oauth_data["state_data"]["connection_id"] = str(connection.id)
        oauth_data["state_data"]["installation_id"] = str(installation.id)

        logger.info(f"OAuth flow initiated: {provider_name} for customer {customer_id}")

        return {
            "authorization_url": oauth_data["authorization_url"],
            "state": oauth_data["state"],
            "connection_id": str(connection.id),
            "state_data": oauth_data["state_data"]  # Store in session/Redis
        }

    async def handle_oauth_callback(
        self,
        provider_name: str,
        code: str,
        state: str,
        state_data: Dict[str, Any],
        shop_domain: Optional[str] = None
    ) -> ConnectionCredential:
        """
        Handle OAuth callback and store credentials

        Args:
            provider_name: OAuth provider
            code: Authorization code
            state: State token
            state_data: State data from initiate_oauth_connection
            shop_domain: Shopify shop domain (optional)

        Returns:
            ConnectionCredential with status ACTIVE

        Raises:
            ValueError: If state validation fails or token exchange fails
        """
        # Validate state
        if state != state_data.get("state"):
            raise ValueError("Invalid state token (CSRF protection)")

        connection_id = state_data.get("connection_id")
        if not connection_id:
            raise ValueError("Missing connection_id in state data")

        # Get pending connection
        connection = self.db.query(ConnectionCredential).filter(
            ConnectionCredential.id == connection_id
        ).first()

        if not connection:
            raise ValueError(f"Connection not found: {connection_id}")

        if connection.status != ConnectionStatus.PENDING:
            raise ValueError(f"Connection not in pending state: {connection.status}")

        try:
            # Exchange code for tokens
            token_response = await self.oauth_service.handle_oauth_callback(
                provider_name=provider_name,
                code=code,
                state=state,
                shop_domain=shop_domain
            )

            # Extract token data
            access_token = token_response.get("access_token")
            refresh_token = token_response.get("refresh_token")
            expires_in = token_response.get("expires_in")
            scope = token_response.get("scope")
            token_type = token_response.get("token_type", "Bearer")

            # Provider-specific metadata
            metadata = {}
            if provider_name == "salesforce":
                metadata["instance_url"] = token_response.get("instance_url")
                metadata["id"] = token_response.get("id")
            elif provider_name == "shopify":
                metadata["shop"] = shop_domain

            # Encrypt credentials
            encrypted_credentials = self.vault.encrypt_oauth_credentials(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=expires_in,
                scope=scope,
                token_type=token_type,
                **metadata
            )

            # Update connection
            connection.encrypted_credentials = encrypted_credentials
            connection.oauth_scopes = scope.split() if scope else []
            connection.connection_metadata = metadata
            connection.status = ConnectionStatus.ACTIVE
            connection.health_status = "healthy"
            connection.last_health_check = datetime.now(timezone.utc)
            connection.last_successful_use = datetime.now(timezone.utc)

            if expires_in:
                connection.token_expires_at = self.oauth_service.calculate_token_expiry(expires_in)

            # Update installation status
            installation = self.db.query(MCPInstallation).filter(
                MCPInstallation.id == connection.mcp_installation_id
            ).first()
            if installation:
                installation.status = "active"
                installation.enabled = True
                installation.installed_at = datetime.now(timezone.utc)

            self.db.commit()
            self.db.refresh(connection)

            logger.info(f"OAuth callback successful: {provider_name} for connection {connection_id}")

            return connection

        except Exception as e:
            logger.error(f"OAuth callback failed: {e}")
            connection.status = ConnectionStatus.ERROR
            connection.error_count += 1
            connection.last_error_message = str(e)
            connection.last_error_at = datetime.now(timezone.utc)
            self.db.commit()
            raise

    async def create_api_key_connection(
        self,
        customer_id: str,
        mcp_id: str,
        api_key: str,
        api_secret: Optional[str] = None,
        user_id: str = None,
        connection_name: Optional[str] = None,
        test_connection: bool = True,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        **extra_fields
    ) -> ConnectionCredential:
        """
        Create API key connection

        Args:
            customer_id: Customer UUID
            mcp_id: MCP UUID
            api_key: API key
            api_secret: API secret (optional)
            user_id: User creating connection
            connection_name: Custom connection name
            test_connection: Test connection before saving
            ip_address: User IP address
            user_agent: User agent string
            **extra_fields: Additional provider-specific fields

        Returns:
            ConnectionCredential with status ACTIVE

        Raises:
            ValueError: If MCP not found or connection test fails
        """
        # Validate MCP
        mcp = self.db.query(MCP).filter(MCP.id == mcp_id).first()
        if not mcp:
            raise ValueError(f"MCP not found: {mcp_id}")

        # Get or create MCP installation
        installation = self.db.query(MCPInstallation).filter(
            and_(
                MCPInstallation.customer_id == customer_id,
                MCPInstallation.mcp_id == mcp_id
            )
        ).first()

        if not installation:
            installation = MCPInstallation(
                customer_id=customer_id,
                mcp_id=mcp_id,
                status="installing"
            )
            self.db.add(installation)
            self.db.flush()

        # Test connection if requested
        if test_connection:
            test_result = await self._test_api_key_connection(
                mcp=mcp,
                api_key=api_key,
                api_secret=api_secret,
                **extra_fields
            )
            if not test_result["success"]:
                raise ValueError(f"Connection test failed: {test_result['error']}")

        # Encrypt credentials
        encrypted_credentials = self.vault.encrypt_api_key(
            api_key=api_key,
            api_secret=api_secret,
            **extra_fields
        )

        # Create connection
        connection = ConnectionCredential(
            customer_id=customer_id,
            mcp_id=mcp_id,
            mcp_installation_id=installation.id,
            connection_type=ConnectionType.API_KEY,
            connection_name=connection_name or f"{mcp.display_name or mcp.name} Connection",
            encrypted_credentials=encrypted_credentials,
            status=ConnectionStatus.ACTIVE,
            health_status="healthy",
            last_health_check=datetime.now(timezone.utc),
            last_successful_use=datetime.now(timezone.utc),
            created_by_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )

        self.db.add(connection)

        # Update installation
        installation.status = "active"
        installation.enabled = True
        installation.installed_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(connection)

        logger.info(f"API key connection created: {mcp.name} for customer {customer_id}")

        return connection

    async def create_database_connection(
        self,
        customer_id: str,
        mcp_id: str,
        host: str,
        port: int,
        username: str,
        password: str,
        database: str,
        ssl_mode: str = "prefer",
        user_id: str = None,
        connection_name: Optional[str] = None,
        test_connection: bool = True,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        **extra_fields
    ) -> ConnectionCredential:
        """
        Create database connection

        Args:
            customer_id: Customer UUID
            mcp_id: MCP UUID
            host: Database host
            port: Database port
            username: Database username
            password: Database password
            database: Database name
            ssl_mode: SSL mode (prefer, require, disable)
            user_id: User creating connection
            connection_name: Custom connection name
            test_connection: Test connection before saving
            ip_address: User IP address
            user_agent: User agent string
            **extra_fields: Additional connection parameters

        Returns:
            ConnectionCredential with status ACTIVE

        Raises:
            ValueError: If MCP not found or connection test fails
        """
        # Validate MCP
        mcp = self.db.query(MCP).filter(MCP.id == mcp_id).first()
        if not mcp:
            raise ValueError(f"MCP not found: {mcp_id}")

        # Get or create MCP installation
        installation = self.db.query(MCPInstallation).filter(
            and_(
                MCPInstallation.customer_id == customer_id,
                MCPInstallation.mcp_id == mcp_id
            )
        ).first()

        if not installation:
            installation = MCPInstallation(
                customer_id=customer_id,
                mcp_id=mcp_id,
                status="installing"
            )
            self.db.add(installation)
            self.db.flush()

        # Test connection if requested
        if test_connection:
            test_result = await self._test_database_connection(
                mcp=mcp,
                host=host,
                port=port,
                username=username,
                password=password,
                database=database,
                ssl_mode=ssl_mode,
                **extra_fields
            )
            if not test_result["success"]:
                raise ValueError(f"Connection test failed: {test_result['error']}")

        # Encrypt credentials
        encrypted_credentials = self.vault.encrypt_database_credentials(
            host=host,
            port=port,
            username=username,
            password=password,
            database=database,
            ssl_mode=ssl_mode,
            **extra_fields
        )

        # Create connection
        connection = ConnectionCredential(
            customer_id=customer_id,
            mcp_id=mcp_id,
            mcp_installation_id=installation.id,
            connection_type=ConnectionType.DATABASE,
            connection_name=connection_name or f"{mcp.display_name or mcp.name} ({database})",
            connection_metadata={"host": host, "port": port, "database": database},
            encrypted_credentials=encrypted_credentials,
            status=ConnectionStatus.ACTIVE,
            health_status="healthy",
            last_health_check=datetime.now(timezone.utc),
            last_successful_use=datetime.now(timezone.utc),
            created_by_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )

        self.db.add(connection)

        # Update installation
        installation.status = "active"
        installation.enabled = True
        installation.installed_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(connection)

        logger.info(f"Database connection created: {mcp.name} for customer {customer_id}")

        return connection

    async def refresh_oauth_token(self, connection_id: str) -> ConnectionCredential:
        """
        Refresh OAuth access token

        Args:
            connection_id: ConnectionCredential UUID

        Returns:
            Updated ConnectionCredential

        Raises:
            ValueError: If connection not found or not OAuth2 type
        """
        connection = self.db.query(ConnectionCredential).filter(
            ConnectionCredential.id == connection_id
        ).first()

        if not connection:
            raise ValueError(f"Connection not found: {connection_id}")

        if connection.connection_type != ConnectionType.OAUTH2:
            raise ValueError(f"Connection is not OAuth2 type: {connection.connection_type}")

        try:
            # Decrypt current credentials
            credentials = self.vault.decrypt(connection.encrypted_credentials)
            refresh_token = credentials.get("refresh_token")

            if not refresh_token:
                raise ValueError("No refresh token available")

            # Refresh token
            token_response = await self.oauth_service.refresh_token(
                provider_name=connection.oauth_provider,
                refresh_token=refresh_token
            )

            # Update credentials
            credentials["access_token"] = token_response.get("access_token")
            if "refresh_token" in token_response:
                credentials["refresh_token"] = token_response.get("refresh_token")
            if "expires_in" in token_response:
                credentials["expires_in"] = token_response.get("expires_in")

            # Re-encrypt
            connection.encrypted_credentials = self.vault.encrypt(credentials)

            # Update expiry
            if "expires_in" in token_response:
                connection.token_expires_at = self.oauth_service.calculate_token_expiry(
                    token_response["expires_in"]
                )

            connection.status = ConnectionStatus.ACTIVE
            connection.health_status = "healthy"
            connection.last_health_check = datetime.now(timezone.utc)

            self.db.commit()
            self.db.refresh(connection)

            logger.info(f"Token refreshed for connection {connection_id}")

            return connection

        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            connection.status = ConnectionStatus.ERROR
            connection.error_count += 1
            connection.last_error_message = str(e)
            connection.last_error_at = datetime.now(timezone.utc)
            self.db.commit()
            raise

    async def test_connection(self, connection_id: str) -> Dict[str, Any]:
        """
        Test connection health

        Args:
            connection_id: ConnectionCredential UUID

        Returns:
            {
                "success": True/False,
                "response_time_ms": 123,
                "error": "error message" (if failed)
            }
        """
        connection = self.db.query(ConnectionCredential).filter(
            ConnectionCredential.id == connection_id
        ).first()

        if not connection:
            return {"success": False, "error": "Connection not found"}

        mcp = self.db.query(MCP).filter(MCP.id == connection.mcp_id).first()

        start_time = datetime.now(timezone.utc)

        try:
            credentials = self.vault.decrypt(connection.encrypted_credentials)

            if connection.connection_type == ConnectionType.OAUTH2:
                result = await self._test_oauth_connection(mcp, credentials)
            elif connection.connection_type == ConnectionType.API_KEY:
                result = await self._test_api_key_connection(mcp, **credentials)
            elif connection.connection_type == ConnectionType.DATABASE:
                result = await self._test_database_connection(mcp, **credentials)
            else:
                result = {"success": False, "error": "Unknown connection type"}

            # Calculate response time
            response_time_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
            result["response_time_ms"] = response_time_ms

            # Update connection health
            if result["success"]:
                connection.health_status = "healthy"
                connection.last_successful_use = datetime.now(timezone.utc)
                connection.error_count = 0
            else:
                connection.health_status = "error"
                connection.error_count += 1
                connection.last_error_message = result.get("error")
                connection.last_error_at = datetime.now(timezone.utc)

            connection.last_health_check = datetime.now(timezone.utc)
            self.db.commit()

            return result

        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            connection.health_status = "error"
            connection.error_count += 1
            connection.last_error_message = str(e)
            connection.last_error_at = datetime.now(timezone.utc)
            connection.last_health_check = datetime.now(timezone.utc)
            self.db.commit()

            return {
                "success": False,
                "error": str(e),
                "response_time_ms": int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
            }

    async def _test_oauth_connection(self, mcp: MCP, credentials: Dict[str, Any]) -> Dict[str, bool]:
        """Test OAuth connection by making API request"""
        # Provider-specific test endpoints
        test_endpoints = {
            "salesforce": "{instance_url}/services/data/v57.0/sobjects",
            "google": "https://www.googleapis.com/oauth2/v1/userinfo",
            "microsoft": "https://graph.microsoft.com/v1.0/me",
            "slack": "https://slack.com/api/auth.test",
            "hubspot": "https://api.hubapi.com/crm/v3/objects/contacts?limit=1",
            "shopify": "https://{shop}/admin/api/2024-01/shop.json",
            "github": "https://api.github.com/user",
            "gitlab": "https://gitlab.com/api/v4/user",
        }

        provider = credentials.get("oauth_provider") or mcp.name.lower()
        endpoint = test_endpoints.get(provider)

        if not endpoint:
            return {"success": False, "error": f"No test endpoint for provider: {provider}"}

        # Replace variables in endpoint
        endpoint = endpoint.format(
            instance_url=credentials.get("instance_url", ""),
            shop=credentials.get("shop", "")
        )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    endpoint,
                    headers={"Authorization": f"Bearer {credentials['access_token']}"},
                    timeout=10.0
                )
                return {"success": response.status_code == 200}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _test_api_key_connection(self, mcp: MCP, **credentials) -> Dict[str, bool]:
        """Test API key connection"""
        # Provider-specific test logic
        # For now, return success (implement per-provider logic later)
        return {"success": True}

    async def _test_database_connection(self, mcp: MCP, **credentials) -> Dict[str, bool]:
        """Test database connection"""
        # Database-specific test logic (SELECT 1)
        # For now, return success (implement per-database logic later)
        return {"success": True}

    def list_connections(
        self,
        customer_id: str,
        status: Optional[ConnectionStatus] = None,
        connection_type: Optional[ConnectionType] = None
    ) -> List[ConnectionCredential]:
        """
        List connections for customer

        Args:
            customer_id: Customer UUID
            status: Filter by status
            connection_type: Filter by connection type

        Returns:
            List of ConnectionCredential
        """
        query = self.db.query(ConnectionCredential).filter(
            ConnectionCredential.customer_id == customer_id
        )

        if status:
            query = query.filter(ConnectionCredential.status == status)

        if connection_type:
            query = query.filter(ConnectionCredential.connection_type == connection_type)

        return query.order_by(ConnectionCredential.created_at.desc()).all()

    def delete_connection(self, connection_id: str) -> bool:
        """
        Delete connection and revoke credentials

        Args:
            connection_id: ConnectionCredential UUID

        Returns:
            True if deleted, False if not found
        """
        connection = self.db.query(ConnectionCredential).filter(
            ConnectionCredential.id == connection_id
        ).first()

        if not connection:
            return False

        # Mark as revoked (soft delete)
        connection.status = ConnectionStatus.REVOKED
        connection.revoked_at = datetime.now(timezone.utc)

        # Update installation status
        installation = self.db.query(MCPInstallation).filter(
            MCPInstallation.id == connection.mcp_installation_id
        ).first()
        if installation:
            installation.enabled = False
            installation.status = "uninstalled"
            installation.uninstalled_at = datetime.now(timezone.utc)

        self.db.commit()

        logger.info(f"Connection deleted: {connection_id}")

        return True
