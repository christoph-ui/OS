"""
Expert model
Represents AI-augmented experts in the marketplace
"""

from sqlalchemy import Column, String, Integer, Text, DECIMAL, DateTime, func, Boolean
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import relationship
import uuid

from ..database import Base


class Expert(Base):
    """Expert model for marketplace"""

    __tablename__ = "experts"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Basic information
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    title = Column(String(255))  # e.g., "Tax Expert & Compliance Specialist"
    bio = Column(Text)

    # Avatar/profile
    avatar_url = Column(String(500))
    avatar_initials = Column(String(5))  # e.g., "MW"

    # Specializations
    specializations = Column(ARRAY(String))  # ["tax", "legal", "finance"]
    mcp_expertise = Column(ARRAY(String))  # ["CTAX", "LAW", "FP&A"]

    # Credentials
    certifications = Column(JSONB)  # List of certifications
    years_experience = Column(Integer)
    education = Column(Text)

    # Rating and reviews
    rating = Column(DECIMAL(3, 2), default=0.0)  # e.g., 4.85
    review_count = Column(Integer, default=0)

    # Performance metrics
    ai_automation_rate = Column(DECIMAL(5, 2), default=0.0)  # e.g., 87.50 = 87.5%
    avg_response_time_hours = Column(DECIMAL(5, 2))  # Average response time in hours
    completed_tasks = Column(Integer, default=0)
    active_clients = Column(Integer, default=0)

    # Pricing
    hourly_rate_cents = Column(Integer, nullable=False)  # Rate in cents (e.g., 18000 = €180)
    currency = Column(String(3), default="EUR")

    # Availability
    available = Column(Boolean, default=True)
    availability_status = Column(String(50))  # "available_now", "busy", "on_vacation"
    max_concurrent_clients = Column(Integer, default=10)

    # Payout information
    total_earnings_cents = Column(Integer, default=0)
    current_month_earnings_cents = Column(Integer, default=0)

    # Status
    status = Column(String(20), default="active")  # active, inactive, suspended
    verified = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_active_at = Column(DateTime(timezone=True))

    # Relationships
    engagements = relationship("Engagement", back_populates="expert", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="expert")

    def __repr__(self):
        return f"<Expert {self.name} - {self.title}>"
