"""
User schemas for API requests/responses
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from ..models.user import UserRole, UserStatus


# ============================================================================
# Base Schemas
# ============================================================================

class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    role: UserRole = UserRole.CUSTOMER_USER


class UserCreate(UserBase):
    """Schema for creating a new user"""
    customer_id: Optional[UUID] = None  # Required for customer users, null for platform admins
    password: str = Field(..., min_length=8, max_length=100)
    permissions: Optional[Dict[str, bool]] = {}

    @validator('customer_id')
    def validate_customer_id(cls, v, values):
        """Validate customer_id based on role"""
        role = values.get('role')
        if role == UserRole.PLATFORM_ADMIN and v is not None:
            raise ValueError("Platform admins cannot belong to a customer")
        if role in [UserRole.CUSTOMER_ADMIN, UserRole.CUSTOMER_USER] and v is None:
            raise ValueError("Customer users must belong to a customer")
        return v


class UserInvite(BaseModel):
    """Schema for inviting a user"""
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    role: UserRole = UserRole.CUSTOMER_USER
    permissions: Optional[Dict[str, bool]] = {}


class UserUpdate(BaseModel):
    """Schema for updating a user"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[UserRole] = None
    permissions: Optional[Dict[str, bool]] = None
    status: Optional[UserStatus] = None


class UserSetPassword(BaseModel):
    """Schema for setting password (after invitation)"""
    token: str
    password: str = Field(..., min_length=8, max_length=100)
    password_confirm: str = Field(..., min_length=8, max_length=100)

    @validator('password_confirm')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v


class UserChangePassword(BaseModel):
    """Schema for changing password"""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)
    new_password_confirm: str = Field(..., min_length=8, max_length=100)

    @validator('new_password_confirm')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


# ============================================================================
# Response Schemas
# ============================================================================

class UserResponse(UserBase):
    """Schema for user response"""
    id: UUID
    customer_id: Optional[UUID]
    partner_id: Optional[UUID]  # For partner admin users
    status: UserStatus
    permissions: Dict[str, bool]
    last_login_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True


class UserDetailResponse(UserResponse):
    """Detailed user response with additional fields"""
    email_verified: bool
    email_verified_at: Optional[datetime]
    login_count: int
    failed_login_attempts: int
    invited_by_id: Optional[UUID]
    invited_at: Optional[datetime]
    invitation_accepted_at: Optional[datetime]

    class Config:
        orm_mode = True
        from_attributes = True


class UserListResponse(BaseModel):
    """Schema for paginated user list"""
    users: list[UserResponse]
    total: int
    page: int
    page_size: int


class UserInvitationResponse(BaseModel):
    """Response after inviting a user"""
    success: bool
    message: str
    user_id: UUID
    invitation_token: Optional[str] = None  # Only in test mode

    class Config:
        orm_mode = True
        from_attributes = True


# ============================================================================
# Permission Schemas
# ============================================================================

class PermissionUpdate(BaseModel):
    """Schema for updating user permissions"""
    permissions: Dict[str, bool]


class PermissionCheck(BaseModel):
    """Schema for checking permissions"""
    permission: str


class PermissionCheckResponse(BaseModel):
    """Response for permission check"""
    has_permission: bool
    permission: str


# ============================================================================
# Auth Context Schema
# ============================================================================

class UserContext(BaseModel):
    """Current user context (used in JWT claims and API responses)"""
    user_id: UUID
    customer_id: Optional[UUID]
    partner_id: Optional[UUID]  # For partner admin users
    email: str
    full_name: str
    role: UserRole
    permissions: Dict[str, bool]
    is_platform_admin: bool
    is_partner_admin: bool

    @classmethod
    def from_user(cls, user):
        """Create context from User model"""
        return cls(
            user_id=user.id,
            customer_id=user.customer_id,
            partner_id=user.partner_id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            permissions=user.permissions or {},
            is_platform_admin=user.is_platform_admin,
            is_partner_admin=user.is_partner_admin
        )
