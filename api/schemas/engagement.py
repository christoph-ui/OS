"""
Engagement schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class EngagementBase(BaseModel):
    """Base engagement schema"""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    focus_area: str
    mcps_used: List[str] = Field(default_factory=list)
    deliverables: Optional[str] = None
    estimated_hours: Optional[int] = None


class EngagementCreate(EngagementBase):
    """Schema for creating an engagement"""
    expert_id: UUID


class EngagementUpdate(BaseModel):
    """Schema for updating engagement"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    focus_area: Optional[str] = None
    mcps_used: Optional[List[str]] = None
    deliverables: Optional[str] = None
    estimated_hours: Optional[int] = None
    status: Optional[str] = None


class EngagementResponse(BaseModel):
    """Schema for engagement response"""
    id: UUID
    customer_id: UUID
    expert_id: UUID
    title: str
    description: Optional[str]
    focus_area: str
    mcps_used: Optional[List[str]]
    deliverables: Optional[str]
    estimated_hours: Optional[int]
    status: str
    tasks_total: int
    tasks_completed: int
    hours_logged: int
    ai_automation_rate: int
    total_cost_cents: int
    current_month_cost_cents: int
    created_at: datetime
    started_at: Optional[datetime]

    model_config = {"from_attributes": True}


class EngagementDetailResponse(EngagementResponse):
    """Detailed engagement response with expert info"""
    expert_name: Optional[str] = None
    expert_title: Optional[str] = None
    expert_avatar_initials: Optional[str] = None
    updated_at: datetime
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class EngagementListResponse(BaseModel):
    """List of engagements"""
    engagements: List[EngagementResponse]
    total: int
