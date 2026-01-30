"""
Customer schemas
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class CustomerBase(BaseModel):
    """Base customer schema"""
    company_name: str = Field(..., min_length=1, max_length=255)
    company_type: Optional[str] = Field(None, max_length=50)
    vat_id: Optional[str] = Field(None, max_length=50)
    street: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: str = Field(default="DE", max_length=2)
    contact_name: str = Field(..., min_length=1, max_length=255)
    contact_email: EmailStr
    contact_phone: Optional[str] = Field(None, max_length=50)


class CustomerCreate(CustomerBase):
    """Schema for creating a new customer"""
    password: str = Field(..., min_length=8)


class CustomerUpdate(BaseModel):
    """Schema for updating customer information"""
    company_name: Optional[str] = Field(None, min_length=1, max_length=255)
    company_type: Optional[str] = Field(None, max_length=50)
    vat_id: Optional[str] = Field(None, max_length=50)
    street: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=2)
    contact_name: Optional[str] = Field(None, min_length=1, max_length=255)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=50)


class CustomerResponse(BaseModel):
    """Schema for customer response"""
    id: UUID
    company_name: str
    company_type: Optional[str]
    contact_name: str
    contact_email: EmailStr
    tier: str
    status: str
    email_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CustomerDetailResponse(CustomerResponse):
    """Detailed customer response with additional fields"""
    vat_id: Optional[str]
    street: Optional[str]
    city: Optional[str]
    postal_code: Optional[str]
    country: str
    contact_phone: Optional[str]
    source: Optional[str]
    sales_owner: Optional[str]
    stripe_customer_id: Optional[str]
    updated_at: datetime

    model_config = {"from_attributes": True}
