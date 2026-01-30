"""
Partner schemas for API requests/responses
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


# ============================================================================
# Partner Schemas
# ============================================================================

class PartnerBase(BaseModel):
    """Base partner schema"""
    company_name: str = Field(..., min_length=1, max_length=255)
    contact_email: EmailStr
    contact_phone: Optional[str] = Field(None, max_length=50)
    street: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: str = Field(default="DE", max_length=2)
    vat_id: Optional[str] = Field(None, max_length=50)


class PartnerCreate(PartnerBase):
    """Schema for creating a new partner"""
    password: str = Field(..., min_length=8, max_length=100)
    contact_name: str = Field(..., min_length=1, max_length=255)  # For creating primary admin user


class PartnerUpdate(BaseModel):
    """Schema for updating partner information"""
    company_name: Optional[str] = Field(None, min_length=1, max_length=255)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=50)
    street: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=2)
    vat_id: Optional[str] = Field(None, max_length=50)


class PartnerResponse(BaseModel):
    """Schema for partner response"""
    id: UUID
    company_name: str
    contact_email: EmailStr
    status: str
    email_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PartnerDetailResponse(PartnerResponse):
    """Detailed partner response with additional fields"""
    contact_phone: Optional[str]
    street: Optional[str]
    city: Optional[str]
    postal_code: Optional[str]
    country: str
    vat_id: Optional[str]
    stripe_connect_account_id: Optional[str]
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Partner Customer Management Schemas
# ============================================================================

class PartnerCustomerCreate(BaseModel):
    """Schema for partner creating a customer"""
    company_name: str = Field(..., min_length=1, max_length=255)
    company_type: Optional[str] = Field(None, max_length=50)
    contact_name: str = Field(..., min_length=1, max_length=255)
    contact_email: EmailStr
    contact_phone: Optional[str] = Field(None, max_length=50)
    vat_id: Optional[str] = Field(None, max_length=50)
    street: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: str = Field(default="DE", max_length=2)
    tier: str = Field(default="starter")  # starter, professional, business, enterprise

    # Auto-generate password or send invitation?
    send_invitation: bool = Field(default=True)


class PartnerCustomerResponse(BaseModel):
    """Schema for customer managed by partner"""
    id: UUID
    company_name: str
    contact_email: EmailStr
    tier: str
    status: str
    partner_id: UUID
    created_at: datetime
    onboarding_status: str

    class Config:
        from_attributes = True


class PartnerCustomerListResponse(BaseModel):
    """Schema for paginated customer list"""
    customers: list[PartnerCustomerResponse]
    total: int
    page: int
    page_size: int


# ============================================================================
# Partner Dashboard Schemas
# ============================================================================

class PartnerDashboardResponse(BaseModel):
    """Partner dashboard statistics"""
    partner_id: UUID
    company_name: str
    total_customers: int
    active_customers: int
    total_revenue: float  # Total revenue from all customers
    customers_onboarding: int  # Customers in onboarding
    recent_customers: list[PartnerCustomerResponse]  # Last 5 customers


# ============================================================================
# Partner Login Schemas
# ============================================================================

class PartnerLoginRequest(BaseModel):
    """Partner login request"""
    email: EmailStr
    password: str


class PartnerLoginResponse(BaseModel):
    """Partner login response"""
    access_token: str
    token_type: str
    partner: PartnerResponse
    user_id: UUID  # Partner admin user ID
