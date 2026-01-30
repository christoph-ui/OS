"""
Partner model
Represents agencies/resellers who manage multiple customer accounts
"""

from sqlalchemy import Column, String, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from ..database import Base


class Partner(Base):
    """Partner (agency/reseller) model"""

    __tablename__ = "partners"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Company information
    company_name = Column(String(255), nullable=False)
    contact_email = Column(String(255), nullable=False, unique=True, index=True)
    contact_phone = Column(String(50))

    # Address
    street = Column(String(255))
    city = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(2), default="DE")
    vat_id = Column(String(50))  # USt-IdNr.

    # Stripe Connect (for revenue share)
    stripe_connect_account_id = Column(String(255), unique=True, index=True)

    # Status
    status = Column(String(20), default="active")  # active, suspended, inactive
    email_verified = Column(Boolean, default=False)
    email_verified_at = Column(DateTime(timezone=True))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    # Customers managed by this partner
    customers = relationship(
        "Customer",
        back_populates="partner",
        foreign_keys="[Customer.partner_id]",
        cascade="all, delete-orphan"
    )

    # Partner admin users
    users = relationship(
        "User",
        back_populates="partner",
        foreign_keys="[User.partner_id]",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Partner {self.company_name} ({self.contact_email})>"

    @property
    def is_active(self) -> bool:
        """Check if partner account is active"""
        return self.status == "active"

    @property
    def customer_count(self) -> int:
        """Get number of managed customers"""
        return len(self.customers) if self.customers else 0
