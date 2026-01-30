"""
Connector Category model
Hierarchical categorization for the marketplace
"""

from sqlalchemy import Column, String, Integer, Text, Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from ..database import Base


class ConnectorCategory(Base):
    """
    Connector Category - Hierarchical marketplace categorization
    
    Structure:
    - data_sources
      - crm (Salesforce, HubSpot)
      - erp (SAP, Oracle)
      - cloud_storage (Google Drive, Dropbox)
      - databases (PostgreSQL, MySQL)
    - ai_models
      - tax (CTAX)
      - legal (LAW)
      - logistics (ETIM)
      - marketing (PUBLISH, MARKET)
    - outputs
      - ecommerce (Shopify, Amazon)
      - publishing (WordPress, Contentful)
      - communication (Slack, Teams)
    """

    __tablename__ = "connector_categories"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Hierarchy
    parent_id = Column(UUID(as_uuid=True), ForeignKey("connector_categories.id"), nullable=True)

    # Identification
    slug = Column(String(50), nullable=False, unique=True, index=True)  # "data_sources", "crm"
    name = Column(String(100), nullable=False)  # "Data Sources", "CRM"
    description = Column(Text)

    # Display
    icon = Column(String(10))  # Emoji
    icon_color = Column(String(50))
    sort_order = Column(Integer, default=0)

    # Visibility
    visible = Column(Boolean, default=True)
    featured = Column(Boolean, default=False)

    # Stats (cached)
    connector_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    parent = relationship("ConnectorCategory", remote_side=[id], back_populates="children")
    children = relationship("ConnectorCategory", back_populates="parent")

    def __repr__(self):
        return f"<ConnectorCategory {self.slug}>"

    @property
    def is_root(self) -> bool:
        """Check if this is a root category"""
        return self.parent_id is None

    @property
    def full_path(self) -> str:
        """Get full category path (e.g., 'data_sources/crm')"""
        if self.parent:
            return f"{self.parent.slug}/{self.slug}"
        return self.slug
