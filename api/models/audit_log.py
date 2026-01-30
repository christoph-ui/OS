"""
Audit log model
Tracks all important actions for compliance and debugging
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship
import uuid

from ..database import Base


class AuditLog(Base):
    """Audit log model"""

    __tablename__ = "audit_log"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), index=True)
    user_id = Column(UUID(as_uuid=True))  # Admin user if internal action

    # Action details
    action = Column(String(100), nullable=False)  # e.g., "subscription.created", "invoice.paid"
    resource_type = Column(String(50))  # e.g., "subscription", "deployment"
    resource_id = Column(UUID(as_uuid=True))
    details = Column(JSONB)  # Additional context as JSON

    # Request info
    ip_address = Column(INET)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    customer = relationship("Customer")

    def __repr__(self):
        return f"<AuditLog {self.action} at {self.created_at}>"
