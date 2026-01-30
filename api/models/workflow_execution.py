"""
Workflow Execution model
Tracks individual workflow runs with full state history
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, func, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from ..database import Base


class WorkflowExecution(Base):
    """Workflow Execution - Individual workflow run instance"""

    __tablename__ = "workflow_executions"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False, index=True)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("workflow_subscriptions.id"), index=True)
    triggered_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))  # Who started it

    # Execution state
    status = Column(String(20), default="pending")  # pending, running, completed, failed, paused, canceled
    current_step = Column(String(100))  # Current node ID in workflow
    current_step_index = Column(Integer, default=0)

    # Input/Output data
    input_data = Column(JSONB)  # Initial input to workflow
    output_data = Column(JSONB)  # Final output from workflow

    # State management (LangGraph state)
    # Stores the full state object that gets passed between nodes
    state_snapshot = Column(JSONB)  # Current state of workflow execution

    # Error handling
    error_message = Column(Text)
    error_step = Column(String(100))  # Which step failed
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    # Performance metrics
    execution_time_ms = Column(Integer)  # Total execution time
    steps_completed = Column(Integer, default=0)
    steps_failed = Column(Integer, default=0)
    steps_skipped = Column(Integer, default=0)

    # Cost tracking (for usage-based pricing)
    cost_cents = Column(Integer, default=0)

    # Trigger information
    trigger_type = Column(String(50), default="manual")  # manual, scheduled, api, webhook
    trigger_metadata = Column(JSONB)  # Additional trigger context

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    customer = relationship("Customer")
    workflow = relationship("Workflow", back_populates="executions")
    subscription = relationship("WorkflowSubscription")
    triggered_by = relationship("User", foreign_keys=[triggered_by_user_id])
    step_logs = relationship("WorkflowStepLog", back_populates="execution", cascade="all, delete-orphan", order_by="WorkflowStepLog.step_index")

    def __repr__(self):
        return f"<WorkflowExecution {self.id} ({self.status})>"

    @property
    def is_running(self) -> bool:
        """Check if execution is currently running"""
        return self.status in ["pending", "running"]

    @property
    def is_complete(self) -> bool:
        """Check if execution completed successfully"""
        return self.status == "completed"

    @property
    def duration_seconds(self) -> float:
        """Calculate execution duration in seconds"""
        if not self.started_at:
            return 0.0

        end_time = self.completed_at or datetime.utcnow()
        duration = (end_time - self.started_at).total_seconds()
        return duration

    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage based on completed steps"""
        total_steps = self.steps_completed + self.steps_failed + max(1, len(self.step_logs))
        if total_steps == 0:
            return 0.0
        return (self.steps_completed / total_steps) * 100.0
