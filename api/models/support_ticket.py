"""
Support ticket model
Represents customer support tickets
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from ..database import Base


class SupportTicket(Base):
    """Support ticket model"""

    __tablename__ = "support_tickets"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True)
    deployment_id = Column(UUID(as_uuid=True), ForeignKey("deployments.id"), index=True)

    # Ticket information
    subject = Column(String(255), nullable=False)
    description = Column(Text)
    priority = Column(String(20), default="normal")  # low, normal, high, urgent
    category = Column(String(50))  # billing, technical, feature_request

    # Status
    status = Column(String(20), default="open")  # open, in_progress, waiting, resolved, closed
    assigned_to = Column(String(255))  # Admin user who owns this ticket

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True))

    # Relationships
    customer = relationship("Customer", back_populates="support_tickets")
    deployment = relationship("Deployment", back_populates="support_tickets")

    def __repr__(self):
        return f"<SupportTicket {self.subject} - {self.status}>"
