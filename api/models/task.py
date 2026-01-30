"""
Task model
Represents individual tasks within expert engagements
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from ..database import Base


class Task(Base):
    """Task within an engagement"""

    __tablename__ = "tasks"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    engagement_id = Column(UUID(as_uuid=True), ForeignKey("engagements.id"), nullable=False, index=True)
    expert_id = Column(UUID(as_uuid=True), ForeignKey("experts.id"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True)

    # Task details
    title = Column(String(255), nullable=False)
    description = Column(Text)
    priority = Column(String(20), default="normal")  # low, normal, high, urgent

    # Status
    status = Column(String(20), default="pending")  # pending, in_progress, review, completed, cancelled

    # AI automation
    ai_automated = Column(Integer, default=0)  # Percentage (0-100)
    ai_confidence = Column(Integer, default=0)  # AI confidence level (0-100)
    mcp_used = Column(String(100))  # Which MCP was used

    # Time tracking
    estimated_hours = Column(Integer)
    actual_hours = Column(Integer, default=0)

    # Cost
    cost_cents = Column(Integer, default=0)

    # Results
    result = Column(JSONB)  # Task result/output
    attachments = Column(JSONB)  # List of attachment URLs

    # Review
    customer_rating = Column(Integer)  # 1-5 stars
    customer_feedback = Column(Text)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    due_date = Column(DateTime(timezone=True))

    # Relationships
    engagement = relationship("Engagement", back_populates="tasks")
    expert = relationship("Expert", back_populates="tasks")

    def __repr__(self):
        return f"<Task {self.title} - {self.status}>"
