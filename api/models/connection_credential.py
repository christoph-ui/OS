"""
Connection Credential Model
Stores encrypted credentials for MCP integrations (OAuth tokens, API keys, etc.)
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, func, Boolean, Text, Enum, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
import enum

from ..database import Base


class ConnectionType(str, enum.Enum):
    """Types of authentication/connection methods"""
    OAUTH2 = "oauth2"
    API_KEY = "api_key"
    SERVICE_ACCOUNT = "service_account"
    DATABASE = "database"
    BASIC_AUTH = "basic_auth"
    BEARER_TOKEN = "bearer_token"


class ConnectionStatus(str, enum.Enum):
    """Connection health status"""
    ACTIVE = "active"
    EXPIRED = "expired"
    INVALID = "invalid"
    REVOKED = "revoked"
    PENDING = "pending"
    ERROR = "error"


class ConnectionCredential(Base):
    """
    Encrypted storage for MCP connection credentials

    Supports multiple auth types:
    - OAuth2: access_token, refresh_token, expires_at
    - API Key: api_key
    - Service Account: service_account_json
    - Database: connection_string or host/port/user/password
    """

    __tablename__ = "connection_credentials"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True)
    mcp_installation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("mcp_installations.id"),
        nullable=False,
        index=True
    )
    mcp_id = Column(UUID(as_uuid=True), ForeignKey("mcps.id"), nullable=False, index=True)

    # Connection type
    connection_type = Column(Enum(ConnectionType), nullable=False)

    # Encrypted credentials (Fernet encrypted)
    # Structure depends on connection_type:
    # - OAuth2: {access_token, refresh_token, expires_at, scope, token_type}
    # - API Key: {api_key, api_secret (optional)}
    # - Service Account: {service_account_json, project_id}
    # - Database: {host, port, username, password, database, ssl_mode}
    # - Basic Auth: {username, password}
    # - Bearer Token: {token}
    encrypted_credentials = Column(Text, nullable=False)  # Fernet encrypted JSON string

    # OAuth-specific fields
    oauth_provider = Column(String(100))  # "salesforce", "google", "microsoft", etc.
    oauth_scopes = Column(JSONB)  # ["read", "write", "admin"]
    token_expires_at = Column(DateTime(timezone=True))  # When access token expires

    # Connection metadata (NOT encrypted, for display/filtering)
    connection_name = Column(String(255))  # User-friendly name (e.g., "Salesforce Production")
    connection_metadata = Column(JSONB)  # {instance_url, org_id, username, etc.}

    # Status
    status = Column(Enum(ConnectionStatus), default=ConnectionStatus.PENDING)
    health_status = Column(String(20), default="unknown")  # healthy, warning, error, unknown
    last_health_check = Column(DateTime(timezone=True))
    last_successful_use = Column(DateTime(timezone=True))

    # Error tracking
    error_count = Column(Integer, default=0)
    last_error_message = Column(Text)
    last_error_at = Column(DateTime(timezone=True))

    # Usage tracking
    total_api_calls = Column(Integer, default=0)

    # Security
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))  # User who created connection
    ip_address = Column(String(45))  # IP address of connection creation
    user_agent = Column(String(500))  # User agent string

    # Rotation tracking (for API keys)
    last_rotated_at = Column(DateTime(timezone=True))
    rotation_interval_days = Column(Integer)  # Auto-rotate after N days

    # Compliance
    consent_given = Column(Boolean, default=True)  # User consented to data access
    consent_at = Column(DateTime(timezone=True))
    data_residency = Column(String(50))  # "EU", "US", "GLOBAL", etc.

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True))  # Overall credential expiration
    revoked_at = Column(DateTime(timezone=True))

    # Relationships
    customer = relationship("Customer")
    mcp = relationship("MCP")
    mcp_installation = relationship("MCPInstallation")
    created_by = relationship("User", foreign_keys=[created_by_id])

    def __repr__(self):
        return f"<ConnectionCredential {self.connection_name} ({self.connection_type})>"

    @property
    def is_expired(self) -> bool:
        """Check if credentials are expired"""
        if not self.token_expires_at:
            return False
        from datetime import datetime, timezone
        return datetime.now(timezone.utc) > self.token_expires_at

    @property
    def needs_refresh(self) -> bool:
        """Check if OAuth token needs refresh (within 5 minutes of expiry)"""
        if not self.token_expires_at or self.connection_type != ConnectionType.OAUTH2:
            return False
        from datetime import datetime, timezone, timedelta
        return datetime.now(timezone.utc) > (self.token_expires_at - timedelta(minutes=5))

    @property
    def is_healthy(self) -> bool:
        """Check if connection is healthy"""
        return (
            self.status == ConnectionStatus.ACTIVE
            and self.health_status == "healthy"
            and not self.is_expired
        )
