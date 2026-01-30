"""
Connector model
Represents integrations available in the marketplace (data sources, AI models, output channels)
"""

from sqlalchemy import Column, String, Integer, BigInteger, Text, DECIMAL, DateTime, func, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import relationship
import uuid

from ..database import Base


class Connector(Base):
    """
    Connector - Any integration in the marketplace
    
    Types:
    - Data Sources (input): CRM, ERP, cloud storage, databases
    - AI Models (processing): Tax, legal, logistics, marketing
    - Output Channels (action): E-commerce, publishing, communication
    """

    __tablename__ = "connectors"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Developer (third-party connector creator)
    developer_id = Column(UUID(as_uuid=True), ForeignKey("connector_developers.id"), nullable=True, index=True)

    # Basic information
    name = Column(String(255), nullable=False, unique=True, index=True)  # e.g., "salesforce", "ctax-de"
    display_name = Column(String(255))  # e.g., "Salesforce CRM", "CTAX-DE v2.4"
    version = Column(String(50))
    description = Column(Text)

    # Categorization
    category = Column(String(100))  # "data_sources", "ai_models", "outputs"
    subcategory = Column(String(100))  # "crm", "tax", "ecommerce"
    tags = Column(ARRAY(String))  # ["german", "tax", "compliance"]

    # Data flow direction
    direction = Column(String(20), default="output")  # "input", "output", "bidirectional"

    # Technical details (for AI connectors)
    model_type = Column(String(50))  # "lora", "full_model", "adapter", "api"
    base_model = Column(String(100))  # e.g., "Qwen2.5-72B"
    model_size_gb = Column(DECIMAL(8, 2))  # Model size in GB

    # Capabilities
    capabilities = Column(JSONB)  # List of capabilities
    supported_languages = Column(ARRAY(String))  # ["de", "en"]
    max_context_length = Column(Integer)  # e.g., 32000

    # Storage (for downloadable connectors)
    minio_bucket = Column(String(255))  # MinIO bucket name
    minio_path = Column(String(500))  # Path within bucket
    model_hash = Column(String(64))  # SHA256 hash for verification
    download_size_bytes = Column(BigInteger)

    # Marketplace info
    icon = Column(String(10))  # Emoji icon
    icon_color = Column(String(50))  # "orange", "blue", etc.
    logo_url = Column(String(500))  # Logo URL (preferred over icon if available)
    featured = Column(Boolean, default=False)
    verified = Column(Boolean, default=False)

    # Pricing (if commercial)
    pricing_model = Column(String(50))  # "free", "subscription", "usage_based"
    price_per_month_cents = Column(Integer)
    price_per_query_cents = Column(Integer)

    # Stats
    install_count = Column(Integer, default=0)
    active_installations = Column(Integer, default=0)
    rating = Column(DECIMAL(3, 2), default=0.0)
    review_count = Column(Integer, default=0)

    # Performance metrics
    avg_automation_rate = Column(DECIMAL(5, 2))  # Average automation rate
    avg_response_time_ms = Column(Integer)  # Average response time

    # Requirements
    min_gpu_memory_gb = Column(Integer)
    min_ram_gb = Column(Integer)
    gpu_required = Column(Boolean, default=False)

    # Connection Configuration
    connection_type = Column(String(50))  # "oauth2", "api_key", "database", "service_account", etc.
    oauth_config = Column(JSONB)  # OAuth provider config
    api_docs_url = Column(String(500))  # Link to API documentation
    setup_instructions = Column(Text)  # How to get credentials (markdown)
    connection_test_endpoint = Column(String(500))  # Endpoint for testing connection health

    # Approval workflow (for third-party connectors)
    approval_status = Column(String(20), default="pending")  # pending, approved, rejected
    submitted_at = Column(DateTime(timezone=True))
    approved_at = Column(DateTime(timezone=True))
    approved_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    rejection_reason = Column(Text)

    # Status
    status = Column(String(20), default="active")  # active, deprecated, beta
    published = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    published_at = Column(DateTime(timezone=True))

    # Relationships
    developer = relationship("ConnectorDeveloper", back_populates="connectors")
    approved_by = relationship("User", foreign_keys=[approved_by_id])
    connections = relationship("Connection", back_populates="connector", cascade="all, delete-orphan")
    reviews = relationship("ConnectorReview", back_populates="connector", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Connector {self.display_name}>"

    @property
    def is_first_party(self) -> bool:
        """Check if connector is developed by 0711 (not third-party)"""
        return self.developer_id is None

    @property
    def is_approved(self) -> bool:
        """Check if connector is approved for marketplace"""
        return self.approval_status == "approved"
    
    @property
    def is_ai_connector(self) -> bool:
        """Check if this is an AI model connector"""
        return self.category == "ai_models"
    
    @property
    def is_data_source(self) -> bool:
        """Check if this is a data source connector"""
        return self.category == "data_sources"


# Backward compatibility alias
MCP = Connector
