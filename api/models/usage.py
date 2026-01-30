"""
Usage metrics model
Tracks customer usage for billing and analytics
"""

from sqlalchemy import Column, Integer, BigInteger, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from ..database import Base


class UsageMetric(Base):
    """Usage metrics model"""

    __tablename__ = "usage_metrics"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    deployment_id = Column(UUID(as_uuid=True), ForeignKey("deployments.id"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True)

    # Time bucket
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end = Column(DateTime(timezone=True), nullable=False)

    # Metrics
    query_count = Column(Integer, default=0)
    mcp_calls = Column(JSONB)  # {"ctax": 150, "law": 42, ...}
    storage_bytes = Column(BigInteger, default=0)
    embedding_tokens = Column(Integer, default=0)
    llm_tokens_input = Column(Integer, default=0)
    llm_tokens_output = Column(Integer, default=0)

    # Computed cost estimate (in cents)
    estimated_cost_cents = Column(Integer)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    deployment = relationship("Deployment", back_populates="usage_metrics")
    customer = relationship("Customer", back_populates="usage_metrics")

    def __repr__(self):
        return f"<UsageMetric {self.period_start} - {self.query_count} queries>"
