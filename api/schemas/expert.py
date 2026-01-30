"""
Expert schemas
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from decimal import Decimal


class ExpertBase(BaseModel):
    """Base expert schema"""
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    title: Optional[str] = Field(None, max_length=255)
    bio: Optional[str] = None
    specializations: List[str] = Field(default_factory=list)
    mcp_expertise: List[str] = Field(default_factory=list)
    years_experience: Optional[int] = None
    hourly_rate_cents: int = Field(..., ge=0)


class ExpertCreate(ExpertBase):
    """Schema for creating an expert"""
    avatar_initials: Optional[str] = Field(None, max_length=5)
    certifications: Optional[dict] = None
    education: Optional[str] = None


class ExpertUpdate(BaseModel):
    """Schema for updating expert information"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    title: Optional[str] = Field(None, max_length=255)
    bio: Optional[str] = None
    specializations: Optional[List[str]] = None
    mcp_expertise: Optional[List[str]] = None
    years_experience: Optional[int] = None
    hourly_rate_cents: Optional[int] = Field(None, ge=0)
    availability_status: Optional[str] = None
    available: Optional[bool] = None


class ExpertResponse(BaseModel):
    """Schema for expert response"""
    id: UUID
    name: str
    email: EmailStr
    title: Optional[str]
    bio: Optional[str]
    avatar_initials: Optional[str]
    specializations: Optional[List[str]]
    mcp_expertise: Optional[List[str]]
    years_experience: Optional[int]
    rating: Decimal
    review_count: int
    ai_automation_rate: Decimal
    avg_response_time_hours: Optional[Decimal]
    completed_tasks: int
    active_clients: int
    hourly_rate_cents: int
    currency: str
    available: bool
    availability_status: Optional[str]
    verified: bool
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ExpertDetailResponse(ExpertResponse):
    """Detailed expert response with additional fields"""
    education: Optional[str]
    certifications: Optional[dict]
    total_earnings_cents: int
    current_month_earnings_cents: int
    last_active_at: Optional[datetime]
    updated_at: datetime

    model_config = {"from_attributes": True}


class ExpertListResponse(BaseModel):
    """List of experts with pagination"""
    experts: List[ExpertResponse]
    total: int
    page: int
    page_size: int
