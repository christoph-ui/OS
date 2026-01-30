"""
Deployment model
Represents customer instances (self-hosted or managed)
"""

from sqlalchemy import Column, String, BigInteger, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
import uuid

from ..database import Base


class Deployment(Base):
    """Deployment (customer instance) model"""

    __tablename__ = "deployments"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True)

    # Deployment information
    name = Column(String(255))
    deployment_type = Column(String(20))  # self_hosted, managed
    version = Column(String(20))

    # Managed deployment details
    cloud_provider = Column(String(20))  # aws, gcp, azure, hetzner
    region = Column(String(50))
    instance_type = Column(String(50))

    # License
    license_key = Column(String(255), unique=True, index=True)
    license_expires_at = Column(DateTime(timezone=True))

    # Status
    status = Column(String(20), default="provisioning")
    # provisioning, active, unhealthy, suspended, terminated
    last_heartbeat_at = Column(DateTime(timezone=True))

    # Resources
    mcps_enabled = Column(ARRAY(String))  # Array of enabled MCP names
    storage_used_bytes = Column(BigInteger, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="deployments")
    usage_metrics = relationship("UsageMetric", back_populates="deployment")
    support_tickets = relationship("SupportTicket", back_populates="deployment")

    def __repr__(self):
        return f"<Deployment {self.name} - {self.status}>"
