"""
Workflow model
Represents workflow templates in the marketplace (separate from MCPs)
Workflows orchestrate multiple MCPs in multi-step processes
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, func, Text, Integer, DECIMAL
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
import uuid

from ..database import Base


class Workflow(Base):
    """Workflow - Orchestrated multi-step processes using MCPs"""

    __tablename__ = "workflows"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Developer (third-party workflow creator)
    # Null = first-party workflow created by 0711
    developer_id = Column(UUID(as_uuid=True), ForeignKey("mcp_developers.id"), nullable=True, index=True)

    # Basic information
    name = Column(String(255), nullable=False, unique=True, index=True)  # e.g., "product-syndication"
    display_name = Column(String(255), nullable=False)  # e.g., "Product Syndication Workflow"
    version = Column(String(50), default="1.0.0")
    description = Column(Text)

    # Categorization
    category = Column(String(100))  # "ecommerce", "compliance", "marketing", "finance"
    subcategory = Column(String(100))
    tags = Column(ARRAY(String))  # ["automation", "product", "syndication"]

    # Visual representation
    icon = Column(String(10), default="🔄")  # Emoji icon
    icon_color = Column(String(50), default="purple")

    # Required MCPs (dependency tracking)
    # Example: ["pim", "etim", "channel"]
    required_mcps = Column(ARRAY(String))

    # Workflow complexity/duration estimates
    estimated_duration_minutes = Column(Integer)  # Average execution time
    complexity_level = Column(String(20))  # "simple", "moderate", "advanced"

    # Marketplace info
    featured = Column(Boolean, default=False)
    verified = Column(Boolean, default=False)

    # Pricing (workflows can be monetized!)
    pricing_model = Column(String(50), default="free")  # "free", "subscription", "usage_based"
    price_per_month_cents = Column(Integer)  # Monthly subscription
    price_per_execution_cents = Column(Integer)  # Per-run cost

    # Stats
    install_count = Column(Integer, default=0)
    active_subscriptions = Column(Integer, default=0)
    total_executions = Column(Integer, default=0)
    rating = Column(DECIMAL(3, 2), default=0.0)
    review_count = Column(Integer, default=0)

    # Performance metrics
    avg_execution_time_ms = Column(Integer)
    success_rate = Column(DECIMAL(5, 2), default=100.0)  # Percentage

    # Approval workflow (for third-party workflows)
    approval_status = Column(String(20), default="pending")  # pending, approved, rejected
    submitted_at = Column(DateTime(timezone=True))
    approved_at = Column(DateTime(timezone=True))
    approved_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    rejection_reason = Column(Text)

    # Status
    status = Column(String(20), default="active")  # active, deprecated, beta, archived
    published = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    published_at = Column(DateTime(timezone=True))

    # Relationships
    developer = relationship("MCPDeveloper", foreign_keys=[developer_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])
    definitions = relationship("WorkflowDefinition", back_populates="workflow", cascade="all, delete-orphan")
    subscriptions = relationship("WorkflowSubscription", back_populates="workflow", cascade="all, delete-orphan")
    executions = relationship("WorkflowExecution", back_populates="workflow")

    def __repr__(self):
        return f"<Workflow {self.display_name}>"

    @property
    def is_first_party(self) -> bool:
        """Check if workflow is created by 0711 (not third-party)"""
        return self.developer_id is None

    @property
    def is_approved(self) -> bool:
        """Check if workflow is approved for marketplace"""
        return self.approval_status == "approved"

    @property
    def can_execute(self) -> bool:
        """Check if workflow can be executed"""
        return self.is_approved and self.published and self.status == "active"
