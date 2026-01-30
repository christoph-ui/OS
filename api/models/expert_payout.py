"""
Expert Payout model
Tracks payments to experts via Stripe Connect
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, func, DECIMAL
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from ..database import Base


class ExpertPayout(Base):
    """
    Expert Payout - Payment record for expert work
    
    Flow:
    1. Customer pays invoice
    2. Platform takes fee (e.g., 15%)
    3. Remaining amount transferred to expert's Stripe account
    4. Payout record tracks the transfer
    """

    __tablename__ = "expert_payouts"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    expert_id = Column(UUID(as_uuid=True), ForeignKey("experts.id"), nullable=False, index=True)
    engagement_id = Column(UUID(as_uuid=True), ForeignKey("engagements.id"), nullable=True, index=True)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=True)

    # Amount breakdown
    gross_amount_cents = Column(Integer, nullable=False)  # Total before fees
    platform_fee_cents = Column(Integer, nullable=False)  # 0711's cut
    processing_fee_cents = Column(Integer, default=0)  # Stripe fees
    net_amount_cents = Column(Integer, nullable=False)  # What expert receives

    # Fee details
    platform_fee_percentage = Column(DECIMAL(5, 2), default=15.00)  # e.g., 15%
    
    # Currency
    currency = Column(String(3), default="EUR")

    # Stripe transfer details
    stripe_transfer_id = Column(String(255), unique=True, index=True)
    stripe_payout_id = Column(String(255))  # When it reaches their bank
    stripe_destination = Column(String(255))  # Expert's Stripe account ID

    # Status
    status = Column(String(20), default="pending")
    # pending -> waiting for customer payment
    # processing -> transfer initiated
    # completed -> money transferred to expert
    # failed -> transfer failed
    # refunded -> customer refunded, payout reversed

    # Error handling
    error_message = Column(Text)
    error_code = Column(String(50))
    retry_count = Column(Integer, default=0)

    # Reference
    description = Column(String(500))
    period_start = Column(DateTime(timezone=True))
    period_end = Column(DateTime(timezone=True))

    # Metadata
    metadata = Column(JSONB)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    initiated_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    failed_at = Column(DateTime(timezone=True))

    # Relationships
    expert = relationship("Expert", back_populates="payouts")
    engagement = relationship("Engagement", back_populates="payouts")
    invoice = relationship("Invoice")

    def __repr__(self):
        return f"<ExpertPayout {self.net_amount_cents/100:.2f} {self.currency} - {self.status}>"

    @property
    def is_completed(self) -> bool:
        return self.status == "completed"

    @property
    def can_retry(self) -> bool:
        return self.status == "failed" and self.retry_count < 3


class ExpertEarnings(Base):
    """
    Expert Earnings - Monthly earnings summary
    """

    __tablename__ = "expert_earnings"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key
    expert_id = Column(UUID(as_uuid=True), ForeignKey("experts.id"), nullable=False, index=True)

    # Period
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)  # 1-12

    # Earnings
    gross_earnings_cents = Column(Integer, default=0)
    platform_fees_cents = Column(Integer, default=0)
    net_earnings_cents = Column(Integer, default=0)
    
    # Activity
    total_tasks = Column(Integer, default=0)
    total_hours = Column(Integer, default=0)
    total_engagements = Column(Integer, default=0)

    # Payouts
    total_payouts_cents = Column(Integer, default=0)
    pending_payouts_cents = Column(Integer, default=0)

    # Currency
    currency = Column(String(3), default="EUR")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    expert = relationship("Expert", back_populates="earnings")

    def __repr__(self):
        return f"<ExpertEarnings {self.year}-{self.month:02d}: {self.net_earnings_cents/100:.2f} {self.currency}>"

    class Meta:
        unique_together = (("expert_id", "year", "month"),)
