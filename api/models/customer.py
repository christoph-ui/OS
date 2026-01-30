"""
Customer model
Represents companies using 0711
"""

from sqlalchemy import Column, String, Boolean, DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from ..database import Base


class Customer(Base):
    """Customer (company) model"""

    __tablename__ = "customers"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Company information
    company_name = Column(String(255), nullable=False)
    company_type = Column(String(50))  # GmbH, AG, UG, etc.
    vat_id = Column(String(50))  # USt-IdNr.

    # Address
    street = Column(String(255))
    city = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(2), default="DE")

    # Primary contact (DEPRECATED - use User model instead)
    # Kept for backward compatibility during migration
    contact_name = Column(String(255), nullable=False)
    contact_email = Column(String(255), nullable=False, unique=True, index=True)
    contact_phone = Column(String(50))

    # Account (DEPRECATED - use User model instead)
    # Kept for backward compatibility during migration
    password_hash = Column(String(255))
    email_verified = Column(Boolean, default=False)
    email_verified_at = Column(DateTime(timezone=True))

    # Primary admin user (set after User table exists)
    primary_admin_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Partner (agency/reseller managing this customer)
    partner_id = Column(
        UUID(as_uuid=True),
        ForeignKey("partners.id", ondelete="SET NULL"),
        nullable=True,  # Null for direct customers (not managed by partner)
        index=True
    )

    # Classification
    tier = Column(String(20), default="starter")  # starter, professional, business, enterprise
    source = Column(String(50))  # website, sales, referral
    sales_owner = Column(String(255))  # for enterprise customers

    # Stripe
    stripe_customer_id = Column(String(255), unique=True, index=True)

    # Status
    status = Column(String(20), default="active")  # active, churned, suspended

    # Enabled connectors (shared services, not deployed per-customer)
    # Example: {"etim": true, "ctax": false, "law": false}
    enabled_connectors = Column(JSONB, default={})

    # Active connections (actively connected via drag-and-drop with direction)
    # Example: {"input": ["pim", "dam", "erp"], "output": ["etim", "syndicate", "tax"]}
    active_connections = Column(JSONB, default={"input": [], "output": []})
    
    # Legacy aliases for backward compatibility
    enabled_mcps = enabled_connectors
    connected_mcps = active_connections

    # Onboarding status tracking
    onboarding_status = Column(String(20), default="not_started")
    # States: not_started, plan_selected, payment_completed, data_uploaded, completed
    onboarding_step = Column(String(50))  # Current step: plan, payment, upload, mcps
    onboarding_data = Column(JSONB, default={})  # Store selected plan, billing cycle, etc.
    onboarding_completed_at = Column(DateTime(timezone=True))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    subscriptions = relationship("Subscription", back_populates="customer", cascade="all, delete-orphan")
    deployments = relationship("Deployment", back_populates="customer", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="customer", cascade="all, delete-orphan")
    usage_metrics = relationship("UsageMetric", back_populates="customer")
    support_tickets = relationship("SupportTicket", back_populates="customer")

    # User management (multi-user support)
    users = relationship("User", back_populates="customer", foreign_keys="[User.customer_id]", cascade="all, delete-orphan")
    primary_admin = relationship("User", foreign_keys=[primary_admin_id], post_update=True)

    # Partner relationship
    partner = relationship("Partner", back_populates="customers", foreign_keys=[partner_id])

    # Marketplace relationships
    engagements = relationship("Engagement", back_populates="customer", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="customer", cascade="all, delete-orphan")
    
    # Connector relationships
    connections = relationship("Connection", back_populates="customer", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Customer {self.company_name} ({self.contact_email})>"
