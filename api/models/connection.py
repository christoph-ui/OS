"""
Connection model
Represents an active connector instance for a customer
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from ..database import Base


class Connection(Base):
    """
    Connection - Active connector instance for a customer
    
    When a customer "installs" a connector from the marketplace,
    a Connection record is created to track:
    - Configuration
    - Credentials (stored separately in ConnectionCredential)
    - Usage metrics
    - Health status
    """

    __tablename__ = "connections"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True)
    connector_id = Column(UUID(as_uuid=True), ForeignKey("connectors.id"), nullable=False, index=True)
    deployment_id = Column(UUID(as_uuid=True), ForeignKey("deployments.id"), nullable=True, index=True)

    # Version tracking
    version_installed = Column(String(50))

    # Configuration
    install_path = Column(String(500))  # For downloadable connectors
    config = Column(JSONB)  # Customer-specific configuration

    # Status
    enabled = Column(Boolean, default=True)
    status = Column(String(20), default="pending")  # pending, active, error, disabled

    # Usage metrics
    total_queries = Column(Integer, default=0)
    last_used_at = Column(DateTime(timezone=True))
    avg_response_time_ms = Column(Integer)
    success_rate = Column(Integer)  # Percentage

    # Health monitoring
    health_status = Column(String(20), default="unknown")  # healthy, degraded, unhealthy, unknown
    last_health_check = Column(DateTime(timezone=True))
    error_message = Column(String(500))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    installed_at = Column(DateTime(timezone=True))
    uninstalled_at = Column(DateTime(timezone=True))

    # Relationships
    customer = relationship("Customer", back_populates="connections")
    connector = relationship("Connector", back_populates="connections")
    deployment = relationship("Deployment", back_populates="connections")
    credentials = relationship("ConnectionCredential", back_populates="connection", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Connection {self.connector_id} for {self.customer_id}>"

    @property
    def is_active(self) -> bool:
        """Check if connection is active and healthy"""
        return self.enabled and self.status == "active" and self.health_status in ("healthy", "unknown")


# Backward compatibility alias
MCPInstallation = Connection
