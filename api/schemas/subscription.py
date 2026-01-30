"""
Subscription schemas
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class SubscriptionBase(BaseModel):
    """Base subscription schema"""
    plan_id: str = Field(..., pattern="^(starter|professional|business|enterprise)$")
    billing_cycle: str = Field(..., pattern="^(monthly|annual)$")


class SubscriptionCreate(SubscriptionBase):
    """Schema for creating a subscription"""
    payment_method_id: Optional[str] = None  # Stripe payment method ID


class SubscriptionResponse(BaseModel):
    """Schema for subscription response"""
    id: UUID
    customer_id: UUID
    plan_id: str
    plan_name: str
    billing_cycle: str
    status: str
    current_period_start: Optional[datetime]
    current_period_end: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}
