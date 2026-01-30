"""
Connector Review model
User reviews and ratings for connectors
"""

from sqlalchemy import Column, String, Integer, Text, Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from ..database import Base


class ConnectorReview(Base):
    """
    Connector Review - User ratings and feedback
    
    Only customers with an active Connection can leave reviews.
    """

    __tablename__ = "connector_reviews"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    connector_id = Column(UUID(as_uuid=True), ForeignKey("connectors.id"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    connection_id = Column(UUID(as_uuid=True), ForeignKey("connections.id"), nullable=True)

    # Rating
    rating = Column(Integer, nullable=False)  # 1-5 stars
    
    # Review content
    title = Column(String(255))
    content = Column(Text)
    
    # Pros/Cons (structured feedback)
    pros = Column(Text)  # What they liked
    cons = Column(Text)  # What could be improved

    # Engagement
    helpful_count = Column(Integer, default=0)
    not_helpful_count = Column(Integer, default=0)

    # Verification
    verified_purchase = Column(Boolean, default=False)  # Has active connection
    featured = Column(Boolean, default=False)  # Highlighted by 0711

    # Developer response
    developer_response = Column(Text)
    developer_responded_at = Column(DateTime(timezone=True))

    # Moderation
    status = Column(String(20), default="published")  # pending, published, hidden, removed
    moderated_at = Column(DateTime(timezone=True))
    moderated_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    moderation_reason = Column(Text)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    connector = relationship("Connector", back_populates="reviews")
    customer = relationship("Customer")
    user = relationship("User", foreign_keys=[user_id])
    connection = relationship("Connection")
    moderated_by = relationship("User", foreign_keys=[moderated_by_id])

    def __repr__(self):
        return f"<ConnectorReview {self.rating}★ for {self.connector_id}>"
