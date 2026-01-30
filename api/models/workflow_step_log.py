"""
Workflow Step Log model
Detailed logs for each step in a workflow execution
Enables debugging, auditing, and performance analysis
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, func, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from ..database import Base


class WorkflowStepLog(Base):
    """Workflow Step Log - Individual step execution record"""

    __tablename__ = "workflow_step_logs"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key to execution
    execution_id = Column(UUID(as_uuid=True), ForeignKey("workflow_executions.id", ondelete="CASCADE"), nullable=False, index=True)

    # Step information
    step_index = Column(Integer, nullable=False)  # Sequential order (0, 1, 2, ...)
    step_id = Column(String(100), nullable=False)  # Node ID from workflow definition
    step_name = Column(String(255))  # Human-readable step name

    # MCP execution details
    mcp_name = Column(String(100))  # Which MCP was called
    mcp_action = Column(String(100))  # Which action/tool was invoked

    # Input/Output
    input_data = Column(JSONB)  # Input to this step
    output_data = Column(JSONB)  # Output from this step

    # Status
    status = Column(String(20), default="pending")  # pending, running, success, failed, skipped, retrying
    error_message = Column(Text)
    retry_attempt = Column(Integer, default=0)  # Which retry attempt (0 = first try)

    # Performance
    duration_ms = Column(Integer)  # How long this step took
    mcp_response_time_ms = Column(Integer)  # MCP-specific response time

    # Timestamps
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    execution = relationship("WorkflowExecution", back_populates="step_logs")

    def __repr__(self):
        return f"<WorkflowStepLog step={self.step_id} status={self.status}>"

    @property
    def is_success(self) -> bool:
        """Check if step completed successfully"""
        return self.status == "success"

    @property
    def is_failed(self) -> bool:
        """Check if step failed"""
        return self.status == "failed"
