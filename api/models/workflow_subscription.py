"""
Workflow Subscription model
Tracks which customers have subscribed to which workflows
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, func, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from ..database import Base


class WorkflowSubscription(Base):
    """Workflow Subscription - Customer's access to a workflow"""

    __tablename__ = "workflow_subscriptions"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True)

    # Subscription status
    enabled = Column(Boolean, default=True)
    status = Column(String(20), default="active")  # active, paused, canceled

    # Workflow-specific configuration
    # Example: {"schedule": "daily 2am", "channels": ["amazon", "google"], "auto_retry": true}
    config = Column(JSONB, default={})

    # Scheduling (optional - for automated workflows)
    schedule_enabled = Column(Boolean, default=False)
    schedule_cron = Column(String(100))  # Cron expression: "0 2 * * *" = daily at 2am
    last_scheduled_run = Column(DateTime(timezone=True))
    next_scheduled_run = Column(DateTime(timezone=True))

    # Usage tracking
    total_executions = Column(Integer, default=0)
    successful_executions = Column(Integer, default=0)
    failed_executions = Column(Integer, default=0)
    last_execution_at = Column(DateTime(timezone=True))

    # Performance
    avg_execution_time_ms = Column(Integer)
    total_cost_cents = Column(Integer, default=0)  # For usage-based pricing

    # Timestamps
    subscribed_at = Column(DateTime(timezone=True), server_default=func.now())
    unsubscribed_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    customer = relationship("Customer")
    workflow = relationship("Workflow", back_populates="subscriptions")

    def __repr__(self):
        return f"<WorkflowSubscription workflow={self.workflow_id} customer={self.customer_id}>"

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_executions == 0:
            return 100.0
        return (self.successful_executions / self.total_executions) * 100.0
