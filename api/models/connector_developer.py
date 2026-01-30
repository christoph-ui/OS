"""
Connector Developer model
Represents third-party developers who create connectors for the marketplace
"""

from sqlalchemy import Column, String, Integer, Boolean, Text, DECIMAL, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from ..database import Base


class ConnectorDeveloper(Base):
    """
    Connector Developer - Third-party developer creating connectors
    
    Developers can:
    - Submit connectors for review
    - Receive payments via Stripe Connect
    - Track connector performance
    """

    __tablename__ = "connector_developers"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Link to user account (optional - can be standalone)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)

    # Basic information
    company_name = Column(String(255), nullable=False)
    developer_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    phone = Column(String(50))

    # Online presence
    website = Column(String(500))
    github_url = Column(String(500))
    linkedin_url = Column(String(500))
    twitter_handle = Column(String(100))

    # Profile
    bio = Column(Text)
    expertise_areas = Column(JSONB)  # ["tax", "legal", "integrations"]

    # Verification
    verified = Column(Boolean, default=False)
    verified_at = Column(DateTime(timezone=True))
    verified_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Stripe Connect (for payouts)
    stripe_account_id = Column(String(255), unique=True, index=True)
    stripe_onboarding_complete = Column(Boolean, default=False)
    revenue_share_percentage = Column(Integer, default=70)  # Developer gets 70%, platform 30%

    # Status
    status = Column(String(20), default="pending")  # pending, active, suspended

    # Stats
    total_connectors = Column(Integer, default=0)
    published_connectors = Column(Integer, default=0)
    total_installations = Column(Integer, default=0)
    avg_rating = Column(DECIMAL(3, 2), default=0.0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_active_at = Column(DateTime(timezone=True))

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    verified_by = relationship("User", foreign_keys=[verified_by_id])
    connectors = relationship("Connector", back_populates="developer")

    def __repr__(self):
        return f"<ConnectorDeveloper {self.company_name}>"


# Backward compatibility alias
MCPDeveloper = ConnectorDeveloper
