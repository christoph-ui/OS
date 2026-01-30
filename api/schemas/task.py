"""
Task schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class TaskBase(BaseModel):
    """Base task schema"""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    priority: str = "normal"
    estimated_hours: Optional[int] = None
    due_date: Optional[datetime] = None


class TaskCreate(TaskBase):
    """Schema for creating a task"""
    engagement_id: UUID


class TaskUpdate(BaseModel):
    """Schema for updating task"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    estimated_hours: Optional[int] = None
    actual_hours: Optional[int] = None
    due_date: Optional[datetime] = None
    result: Optional[dict] = None
    attachments: Optional[dict] = None


class TaskResponse(BaseModel):
    """Schema for task response"""
    id: UUID
    engagement_id: UUID
    expert_id: UUID
    customer_id: UUID
    title: str
    description: Optional[str]
    priority: str
    status: str
    ai_automated: int
    ai_confidence: int
    mcp_used: Optional[str]
    estimated_hours: Optional[int]
    actual_hours: int
    cost_cents: int
    customer_rating: Optional[int]
    created_at: datetime
    due_date: Optional[datetime]

    model_config = {"from_attributes": True}


class TaskDetailResponse(TaskResponse):
    """Detailed task response with additional fields"""
    result: Optional[dict]
    attachments: Optional[dict]
    customer_feedback: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    """List of tasks"""
    tasks: List[TaskResponse]
    total: int


class TaskRatingRequest(BaseModel):
    """Request to rate a task"""
    rating: int = Field(..., ge=1, le=5)
    feedback: Optional[str] = None
