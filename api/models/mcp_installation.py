"""
MCP Installation model
Tracks which customers have installed which MCPs
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, func, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from ..database import Base


class MCPInstallation(Base):
    """MCP installation record for a customer"""

    __tablename__ = "mcp_installations"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True)
    mcp_id = Column(UUID(as_uuid=True), ForeignKey("mcps.id"), nullable=False, index=True)
    deployment_id = Column(UUID(as_uuid=True), ForeignKey("deployments.id"), index=True)

    # Installation details
    version_installed = Column(String(50))
    install_path = Column(String(500))  # Local path where MCP is installed

    # Configuration
    config = Column(JSONB)  # MCP-specific configuration
    enabled = Column(Boolean, default=True)

    # Status
    status = Column(String(20), default="installing")  # installing, active, updating, failed, uninstalled

    # Usage tracking
    total_queries = Column(Integer, default=0)
    last_used_at = Column(DateTime(timezone=True))

    # Performance
    avg_response_time_ms = Column(Integer)
    success_rate = Column(Integer, default=100)  # Percentage

    # Health
    health_status = Column(String(20), default="unknown")  # healthy, warning, error, unknown
    last_health_check = Column(DateTime(timezone=True))
    error_message = Column(String(500))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    installed_at = Column(DateTime(timezone=True))
    uninstalled_at = Column(DateTime(timezone=True))

    # Relationships
    mcp = relationship("MCP", back_populates="installations")

    def __repr__(self):
        return f"<MCPInstallation {self.mcp_id} for customer {self.customer_id}>"
