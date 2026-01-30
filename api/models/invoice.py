"""
Invoice model
Represents invoices (Rechnungen) for German market
"""

from sqlalchemy import Column, String, Integer, Date, DateTime, ForeignKey, func, DECIMAL
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from ..database import Base


class Invoice(Base):
    """Invoice (Rechnung) model"""

    __tablename__ = "invoices"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("subscriptions.id"), index=True)

    # Invoice details
    invoice_number = Column(String(50), unique=True, nullable=False, index=True)
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)

    # Amounts (in cents)
    subtotal_cents = Column(Integer, nullable=False)
    vat_rate = Column(DECIMAL(5, 2), default=19.00)
    vat_cents = Column(Integer, nullable=False)
    total_cents = Column(Integer, nullable=False)
    currency = Column(String(3), default="EUR")

    # Line items (stored as JSON)
    line_items = Column(JSONB, nullable=False)

    # Payment
    payment_method = Column(String(20))  # card, invoice, sepa
    payment_status = Column(String(20), default="pending")  # pending, paid, overdue, void
    paid_at = Column(DateTime(timezone=True))

    # PDF
    pdf_url = Column(String(500))

    # Stripe (if card payment)
    stripe_invoice_id = Column(String(255), unique=True, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="invoices")
    subscription = relationship("Subscription", back_populates="invoices")

    def __repr__(self):
        return f"<Invoice {self.invoice_number} - {self.payment_status}>"
