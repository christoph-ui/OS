"""
MCP Developer model
Represents third-party developers who create and publish MCPs to the marketplace
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, func, Text, Integer, DECIMAL
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from ..database import Base


class MCPDeveloper(Base):
    """MCP Developer - Third-party MCP creators"""

    __tablename__ = "mcp_developers"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Optional link to User (if developer also has platform account)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)

    # Company/individual information
    company_name = Column(String(255), nullable=False)
    developer_name = Column(String(255), nullable=False)  # Contact person
    email = Column(String(255), nullable=False, unique=True, index=True)
    phone = Column(String(50))

    # Online presence
    website = Column(String(500))
    github_url = Column(String(500))
    linkedin_url = Column(String(500))
    twitter_handle = Column(String(100))

    # Description and expertise
    bio = Column(Text)  # Developer bio/description
    expertise_areas = Column(JSONB)  # List of expertise areas (e.g., ["tax", "legal", "finance"])

    # Verification status
    verified = Column(Boolean, default=False)
    verified_at = Column(DateTime(timezone=True))
    verified_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))  # Platform admin who verified

    # Stripe Connect for revenue sharing
    stripe_account_id = Column(String(255), unique=True, index=True)
    stripe_onboarding_complete = Column(Boolean, default=False)
    revenue_share_percentage = Column(Integer, default=70)  # Developer gets 70%, 0711 gets 30%

    # Status
    status = Column(String(20), default="pending")  # pending, active, suspended, banned

    # Stats
    total_mcps = Column(Integer, default=0)
    published_mcps = Column(Integer, default=0)
    total_installations = Column(Integer, default=0)
    avg_rating = Column(DECIMAL(3, 2), default=0.0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_active_at = Column(DateTime(timezone=True))

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    verified_by = relationship("User", foreign_keys=[verified_by_id])
    mcps = relationship("MCP", back_populates="developer", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<MCPDeveloper {self.company_name} ({self.email})>"

    @property
    def is_verified(self) -> bool:
        """Check if developer is verified"""
        return self.verified and self.status == "active"

    @property
    def can_publish(self) -> bool:
        """Check if developer can publish MCPs"""
        return self.is_verified and self.stripe_onboarding_complete
