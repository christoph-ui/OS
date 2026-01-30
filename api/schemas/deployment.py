"""
Deployment schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class DeploymentBase(BaseModel):
    """Base deployment schema"""
    name: str = Field(..., min_length=1, max_length=255)
    deployment_type: str = Field(..., pattern="^(self_hosted|managed)$")
    cloud_provider: Optional[str] = None
    region: Optional[str] = None
    mcps_enabled: List[str] = Field(default_factory=list)


class DeploymentCreate(DeploymentBase):
    """Schema for creating a deployment"""
    customer_id: Optional[UUID] = None  # Optional for partner-managed deployments


class DeploymentResponse(BaseModel):
    """Schema for deployment response"""
    id: UUID
    customer_id: UUID
    name: str
    deployment_type: str
    version: Optional[str]
    status: str
    license_key: Optional[str]
    license_expires_at: Optional[datetime]
    mcps_enabled: Optional[List[str]]
    storage_used_bytes: int
    last_heartbeat_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True
