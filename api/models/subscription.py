"""
Subscription model
Represents customer subscription plans and billing
"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from ..database import Base


class Subscription(Base):
    """Subscription model"""

    __tablename__ = "subscriptions"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True)

    # Plan information
    plan_id = Column(String(50), nullable=False)  # starter, professional, business, enterprise
    plan_name = Column(String(100))

    # Pricing (amounts in cents)
    price_monthly_cents = Column(Integer)
    price_annual_cents = Column(Integer)
    billing_cycle = Column(String(20))  # monthly, annual
    currency = Column(String(3), default="EUR")

    # Stripe integration
    stripe_subscription_id = Column(String(255), unique=True, index=True)
    stripe_price_id = Column(String(255))

    # Status and dates
    status = Column(String(20), default="active")  # trialing, active, past_due, canceled
    trial_ends_at = Column(DateTime(timezone=True))
    current_period_start = Column(DateTime(timezone=True))
    current_period_end = Column(DateTime(timezone=True))
    canceled_at = Column(DateTime(timezone=True))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="subscriptions")
    invoices = relationship("Invoice", back_populates="subscription")

    def __repr__(self):
        return f"<Subscription {self.plan_name} - {self.status}>"
