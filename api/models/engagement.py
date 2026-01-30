"""
Engagement model
Represents customer-expert engagements
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship, synonym
import uuid

from ..database import Base


class Engagement(Base):
    """Engagement between customer and expert"""

    __tablename__ = "engagements"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True)
    expert_id = Column(UUID(as_uuid=True), ForeignKey("experts.id"), nullable=False, index=True)

    # Engagement details
    title = Column(String(255), nullable=False)  # e.g., "Q4 Tax Filing & Planning"
    description = Column(Text)
    focus_area = Column(String(255))  # e.g., "Tax & Compliance"

    # Scope
    connectors_used = Column(ARRAY(String))  # Connectors being utilized in this engagement
    deliverables = Column(Text)  # Description of deliverables
    estimated_hours = Column(Integer)

    # Legacy alias
    mcps_used = synonym('connectors_used')

    # Status
    status = Column(String(20), default="active")  # pending, active, paused, completed, cancelled

    # Metrics
    tasks_total = Column(Integer, default=0)
    tasks_completed = Column(Integer, default=0)
    hours_logged = Column(Integer, default=0)
    ai_automation_rate = Column(Integer, default=0)  # Percentage

    # Billing
    total_cost_cents = Column(Integer, default=0)
    current_month_cost_cents = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    # Relationships
    customer = relationship("Customer", back_populates="engagements")
    expert = relationship("Expert", back_populates="engagements")
    tasks = relationship("Task", back_populates="engagement", cascade="all, delete-orphan")
    booking = relationship("Booking", back_populates="engagement", uselist=False)
    payouts = relationship("ExpertPayout", back_populates="engagement")

    def __repr__(self):
        return f"<Engagement {self.title} - {self.status}>"
