"""
Booking model
Represents a customer's request to work with an expert
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import relationship
import uuid

from ..database import Base


class Booking(Base):
    """
    Booking - Customer request to engage an expert
    
    Flow:
    1. Customer browses experts
    2. Customer creates booking request
    3. Expert reviews and accepts/declines
    4. If accepted, Engagement is created
    5. Work happens via Tasks
    6. Payment processed on completion
    """

    __tablename__ = "bookings"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True)
    expert_id = Column(UUID(as_uuid=True), ForeignKey("experts.id"), nullable=False, index=True)

    # Request details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    connector_focus = Column(ARRAY(String))  # Which connectors they need help with

    # Scope
    project_type = Column(String(50))  # "one_time", "ongoing", "consultation"
    estimated_hours = Column(Integer)
    budget_min_cents = Column(Integer)
    budget_max_cents = Column(Integer)

    # Scheduling
    urgency = Column(String(20), default="normal")  # flexible, normal, urgent, asap
    requested_start = Column(DateTime(timezone=True))
    preferred_times = Column(JSONB)  # [{day: "monday", time: "morning"}, ...]
    timezone = Column(String(50))

    # Attachments/context
    attachments = Column(JSONB)  # [{filename, url, size}, ...]
    context_data = Column(JSONB)  # Additional context

    # Status workflow
    status = Column(String(20), default="pending")
    # pending -> expert reviews
    # accepted -> expert wants to proceed
    # declined -> expert can't help
    # negotiating -> back and forth
    # confirmed -> both agreed, engagement created
    # cancelled -> customer cancelled
    # expired -> no response in time

    # Expert response
    expert_message = Column(Text)
    proposed_rate_cents = Column(Integer)  # Hourly or fixed
    proposed_hours = Column(Integer)
    proposed_start = Column(DateTime(timezone=True))
    counter_proposal = Column(JSONB)  # Full counter-proposal details

    # Response timestamps
    viewed_at = Column(DateTime(timezone=True))
    responded_at = Column(DateTime(timezone=True))
    accepted_at = Column(DateTime(timezone=True))
    declined_at = Column(DateTime(timezone=True))
    declined_reason = Column(Text)

    # Resulting engagement
    engagement_id = Column(UUID(as_uuid=True), ForeignKey("engagements.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True))  # Auto-expire if no response

    # Relationships
    customer = relationship("Customer", back_populates="bookings")
    expert = relationship("Expert", back_populates="bookings")
    engagement = relationship("Engagement", back_populates="booking")

    def __repr__(self):
        return f"<Booking {self.title} - {self.status}>"

    @property
    def is_pending(self) -> bool:
        return self.status == "pending"

    @property
    def is_accepted(self) -> bool:
        return self.status in ("accepted", "confirmed")

    @property
    def can_respond(self) -> bool:
        """Expert can still respond"""
        return self.status in ("pending", "negotiating")


class ExpertAvailability(Base):
    """
    Expert Availability - Weekly schedule
    """

    __tablename__ = "expert_availability"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key
    expert_id = Column(UUID(as_uuid=True), ForeignKey("experts.id"), nullable=False, index=True)

    # Schedule
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = Column(String(5), nullable=False)  # "09:00"
    end_time = Column(String(5), nullable=False)  # "17:00"
    timezone = Column(String(50), default="Europe/Berlin")

    # Slot details
    slot_duration_minutes = Column(Integer, default=60)  # Booking slots
    buffer_minutes = Column(Integer, default=15)  # Buffer between bookings

    # Status
    is_active = Column(Boolean, default=True)

    # Relationships
    expert = relationship("Expert", back_populates="availability_slots")

    def __repr__(self):
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        return f"<ExpertAvailability {days[self.day_of_week]} {self.start_time}-{self.end_time}>"


class ExpertBlockedTime(Base):
    """
    Expert Blocked Time - Specific dates/times unavailable
    """

    __tablename__ = "expert_blocked_times"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key
    expert_id = Column(UUID(as_uuid=True), ForeignKey("experts.id"), nullable=False, index=True)

    # Blocked period
    start_datetime = Column(DateTime(timezone=True), nullable=False)
    end_datetime = Column(DateTime(timezone=True), nullable=False)
    reason = Column(String(255))  # "vacation", "meeting", etc.
    is_recurring = Column(Boolean, default=False)
    recurrence_rule = Column(String(255))  # iCal RRULE format

    # Relationships
    expert = relationship("Expert", back_populates="blocked_times")

    def __repr__(self):
        return f"<ExpertBlockedTime {self.start_datetime} - {self.end_datetime}>"


# Import Boolean for ExpertAvailability
from sqlalchemy import Boolean
