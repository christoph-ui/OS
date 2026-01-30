"""
Authentication Models

User and token models for authentication.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
import uuid


class UserBase(BaseModel):
    """Base user model"""
    email: EmailStr
    name: str
    customer_id: str = Field(description="Customer/tenant ID for multi-tenancy")


class UserCreate(UserBase):
    """User creation request"""
    password: str = Field(min_length=8)


class UserLogin(BaseModel):
    """User login request"""
    email: EmailStr
    password: str


class User(UserBase):
    """Full user model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    is_active: bool = True
    is_admin: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

    # Permissions
    allowed_mcps: List[str] = Field(default_factory=lambda: ["ctax", "law", "tender"])

    class Config:
        from_attributes = True


class UserInDB(User):
    """User model with hashed password (stored in DB)"""
    hashed_password: str


class TokenData(BaseModel):
    """JWT token payload data"""
    user_id: str
    email: str
    customer_id: str
    is_admin: bool = False
    exp: Optional[datetime] = None


class Token(BaseModel):
    """Token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: User


class CustomerContext(BaseModel):
    """
    Customer context for multi-tenancy.

    Passed through requests to ensure data isolation.
    """
    customer_id: str
    user_id: str
    user_email: str
    is_admin: bool = False
    allowed_mcps: List[str] = Field(default_factory=list)

    def can_access_mcp(self, mcp_id: str) -> bool:
        """Check if user can access an MCP"""
        if self.is_admin:
            return True
        return mcp_id in self.allowed_mcps
