"""
User Management Routes
Handles team member invitations, role management, permissions
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID
import secrets

from ..database import get_db
from ..models.user import User, UserRole, UserStatus
from ..models.customer import Customer
from ..schemas.user import (
    UserResponse,
    UserDetailResponse,
    UserListResponse,
    UserInvite,
    UserUpdate,
    UserSetPassword,
    UserChangePassword,
    PermissionUpdate,
    UserInvitationResponse
)
from ..utils.security import (
    get_current_user,
    get_current_customer,
    require_role,
    hash_password,
    verify_password
)
from ..services.email_service import EmailService
import redis
import os
from ..config import settings

router = APIRouter(prefix="/api/users", tags=["users"])

# Redis client for invitation tokens
redis_client = redis.from_url(settings.redis_url, decode_responses=True)


@router.get("/", response_model=UserListResponse)
async def list_team_members(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: Optional[UserRole] = None,
    status: Optional[UserStatus] = None,
    user: User = Depends(get_current_user),
    customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    List team members for current customer

    Requires: customer_admin role
    """
    # Only customer admins can list users
    if user.role != UserRole.CUSTOMER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customer administrators can manage team members"
        )

    # Query users for this customer
    query = db.query(User).filter(User.customer_id == customer.id)

    if role:
        query = query.filter(User.role == role)

    if status:
        query = query.filter(User.status == status)

    # Get total count
    total = query.count()

    # Paginate
    users = query.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return UserListResponse(
        users=[UserResponse.from_orm(u) for u in users],
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/invite", response_model=UserInvitationResponse)
async def invite_team_member(
    invitation: UserInvite,
    user: User = Depends(get_current_user),
    customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Invite a new team member

    Requires: customer_admin role or users.invite permission
    """
    # Check permission
    if user.role != UserRole.CUSTOMER_ADMIN and not user.has_permission("users.invite"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to invite users"
        )

    # Check if email already exists
    existing = db.query(User).filter(User.email == invitation.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )

    # Validate role (can't invite platform admins)
    if invitation.role == UserRole.PLATFORM_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot invite platform administrators"
        )

    testing_mode = os.getenv("TESTING", "false").lower() == "true"

    # Create user in invited state
    new_user = User(
        customer_id=customer.id,
        email=invitation.email,
        first_name=invitation.first_name,
        last_name=invitation.last_name,
        role=invitation.role,
        status=UserStatus.INVITED,
        permissions=invitation.permissions or {},
        invited_by_id=user.id,
        invited_at=datetime.utcnow(),
        email_verified=False
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Generate invitation token
    invite_token = secrets.token_urlsafe(32)

    # Store token in Redis (7 days expiration)
    redis_client.setex(
        f"invite:{invite_token}",
        timedelta(days=7),
        str(new_user.id)
    )

    if testing_mode:
        # Test mode: Return token in response
        return UserInvitationResponse(
            success=True,
            message=f"User invited: {new_user.email}",
            user_id=new_user.id,
            invitation_token=invite_token
        )

    # Production mode: Send invitation email
    await EmailService.send_invitation_email(
        email=new_user.email,
        name=new_user.full_name,
        inviter_name=user.full_name,
        company_name=customer.company_name,
        token=invite_token
    )

    return UserInvitationResponse(
        success=True,
        message=f"Invitation sent to {new_user.email}",
        user_id=new_user.id
    )


@router.post("/accept-invitation", response_model=UserResponse)
async def accept_invitation(
    request: UserSetPassword,
    db: Session = Depends(get_db)
):
    """
    Accept invitation and set password

    User provides invitation token and sets their password
    """
    # Get user ID from Redis
    user_id = redis_client.get(f"invite:{request.token}")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired invitation link"
        )

    # Get user
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if user.status != UserStatus.INVITED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation already accepted"
        )

    # Set password and activate
    user.password_hash = hash_password(request.password)
    user.status = UserStatus.ACTIVE
    user.email_verified = True
    user.email_verified_at = datetime.utcnow()
    user.invitation_accepted_at = datetime.utcnow()

    db.commit()
    db.refresh(user)

    # Delete token from Redis
    redis_client.delete(f"invite:{request.token}")

    return UserResponse.from_orm(user)


@router.get("/{user_id}", response_model=UserDetailResponse)
async def get_user(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user details

    Users can view their own details. Admins can view any user in their org.
    """
    target_user = db.query(User).filter(User.id == user_id).first()

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check permission: Can view own profile or same customer (if admin)
    if target_user.id != current_user.id:
        if current_user.role == UserRole.PLATFORM_ADMIN:
            # Platform admins can view any user
            pass
        elif current_user.customer_id == target_user.customer_id and current_user.role == UserRole.CUSTOMER_ADMIN:
            # Customer admins can view users in their org
            pass
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this user"
            )

    return UserDetailResponse.from_orm(target_user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    updates: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user details

    Requires: customer_admin role
    """
    target_user = db.query(User).filter(User.id == user_id).first()

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check permission
    if current_user.role == UserRole.PLATFORM_ADMIN:
        # Platform admins can update any user
        pass
    elif current_user.customer_id == target_user.customer_id and current_user.role == UserRole.CUSTOMER_ADMIN:
        # Customer admins can update users in their org
        pass
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this user"
        )

    # Apply updates
    if updates.first_name is not None:
        target_user.first_name = updates.first_name

    if updates.last_name is not None:
        target_user.last_name = updates.last_name

    if updates.role is not None:
        # Can't promote to platform admin
        if updates.role == UserRole.PLATFORM_ADMIN and current_user.role != UserRole.PLATFORM_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot promote users to platform admin"
            )
        target_user.role = updates.role

    if updates.permissions is not None:
        target_user.permissions = updates.permissions

    if updates.status is not None:
        target_user.status = updates.status

    target_user.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(target_user)

    return UserResponse.from_orm(target_user)


@router.delete("/{user_id}")
async def remove_user(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Remove (soft delete) a user

    Requires: customer_admin role
    """
    if current_user.role != UserRole.CUSTOMER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customer administrators can remove users"
        )

    target_user = db.query(User).filter(
        User.id == user_id,
        User.customer_id == customer.id
    ).first()

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Can't remove yourself
    if target_user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove yourself"
        )

    # Can't remove primary admin
    if target_user.id == customer.primary_admin_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove primary administrator. Transfer admin rights first."
        )

    # Soft delete
    target_user.status = UserStatus.INACTIVE
    target_user.deleted_at = datetime.utcnow()

    db.commit()

    return {"message": f"User {target_user.email} removed"}


@router.post("/change-password")
async def change_password(
    request: UserChangePassword,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change current user's password

    Requires current password verification
    """
    # Verify current password
    if not verify_password(request.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )

    # Set new password
    user.password_hash = hash_password(request.new_password)
    user.updated_at = datetime.utcnow()

    db.commit()

    return {"message": "Password changed successfully"}


@router.patch("/{user_id}/permissions", response_model=UserResponse)
async def update_user_permissions(
    user_id: UUID,
    permission_update: PermissionUpdate,
    current_user: User = Depends(get_current_user),
    customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Update user permissions

    Requires: customer_admin role
    """
    if current_user.role != UserRole.CUSTOMER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customer administrators can update permissions"
        )

    target_user = db.query(User).filter(
        User.id == user_id,
        User.customer_id == customer.id
    ).first()

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update permissions
    target_user.permissions = permission_update.permissions
    target_user.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(target_user)

    return UserResponse.from_orm(target_user)
