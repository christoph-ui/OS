"""
Medusa Registration model
Represents users who registered to download 0711 Medusa app
"""

from sqlalchemy import Column, String, Integer, DateTime, func

from ..database import Base


class MedusaRegistration(Base):
    """Medusa registration model for download tracking"""

    __tablename__ = "medusa_registrations"

    # Primary key (UUID as string)
    id = Column(String, primary_key=True)

    # User information
    email = Column(String(255), nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    company = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=False)

    # Address
    address = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    postal_code = Column(String(20), nullable=False)
    country = Column(String(2), nullable=False)

    # Download tracking
    download_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<MedusaRegistration {self.full_name} ({self.email})>"
