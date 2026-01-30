"""
Authentication routes
Handles signup, login, email verification
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
import secrets
from datetime import datetime, timedelta
import redis
import os

from ..database import get_db
from ..models.customer import Customer
from ..models.user import User, UserRole, UserStatus
from ..schemas.customer import CustomerCreate, CustomerResponse
from ..schemas.user import UserResponse, UserContext
from ..services.email_service import EmailService
from ..utils.security import hash_password, verify_password, create_access_token
from ..config import settings
import uuid

router = APIRouter()

# Redis client for verification tokens
redis_client = redis.from_url(settings.redis_url, decode_responses=True)


class SignupResponse(BaseModel):
    """Signup response"""
    message: str
    customer_id: str
    token: Optional[str] = None  # Included in test mode


class LoginRequest(BaseModel):
    """Login request"""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Login response"""
    access_token: str
    token_type: str
    user: UserResponse
    customer: Optional[CustomerResponse] = None  # Null for platform admins


class VerifyEmailRequest(BaseModel):
    """Email verification request"""
    token: str


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    customer_data: CustomerCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new customer

    Creates a customer account + primary admin user and sends email verification
    """
    # Check if email already exists (check both User and legacy Customer)
    existing_user = db.query(User).filter(User.email == customer_data.contact_email).first()
    existing_customer = db.query(Customer).filter(
        Customer.contact_email == customer_data.contact_email
    ).first()

    if existing_user or existing_customer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="E-Mail bereits registriert"
        )

    # Auto-verify emails (SMTP not configured yet)
    # TODO: Remove this when SMTP is properly configured in production

    # Create customer (company)
    customer = Customer(
        company_name=customer_data.company_name,
        company_type=customer_data.company_type,
        vat_id=customer_data.vat_id,
        street=customer_data.street,
        city=customer_data.city,
        postal_code=customer_data.postal_code,
        country=customer_data.country,
        contact_name=customer_data.contact_name,
        contact_email=customer_data.contact_email,
        contact_phone=customer_data.contact_phone,
        # Keep password_hash for backward compatibility (deprecated)
        password_hash=hash_password(customer_data.password),
        tier="starter",
        source="website",
        status="active",
        email_verified=True,  # Auto-verify (SMTP placeholder workaround)
        # Initialize onboarding tracking
        onboarding_status="not_started",
        onboarding_step="plan",
        onboarding_data={}
    )

    db.add(customer)
    db.flush()  # Get customer.id without committing

    # Split contact_name into first_name and last_name
    name_parts = customer_data.contact_name.strip().split(' ', 1) if customer_data.contact_name else ['', '']
    first_name = name_parts[0] or 'Admin'
    last_name = name_parts[1] if len(name_parts) > 1 else ''

    # Create primary admin user
    admin_user = User(
        id=uuid.uuid4(),
        customer_id=customer.id,
        email=customer_data.contact_email,
        password_hash=hash_password(customer_data.password),
        first_name=first_name,
        last_name=last_name,
        role=UserRole.CUSTOMER_ADMIN,
        status=UserStatus.ACTIVE,  # Auto-activate (SMTP placeholder workaround)
        permissions={
            "billing.view": True,
            "billing.edit": True,
            "users.invite": True,
            "users.manage": True,
            "mcps.install": True,
            "data.view": True,
            "data.edit": True
        },
        email_verified=True  # Auto-verify (SMTP placeholder workaround)
    )

    db.add(admin_user)
    db.flush()  # Get admin_user.id

    # Set as primary admin
    customer.primary_admin_id = admin_user.id

    db.commit()
    db.refresh(customer)
    db.refresh(admin_user)

    # Return token immediately (email already auto-verified)
    token = create_access_token(data={
        "sub": str(admin_user.id),
        "user_id": str(admin_user.id),
        "email": admin_user.email,
        "customer_id": str(customer.id),
        "role": admin_user.role.value
    })

    return SignupResponse(
        message="Konto erfolgreich erstellt",
        customer_id=str(customer.id),
        token=token
    )


@router.post("/verify-email")
async def verify_email(
    request: VerifyEmailRequest,
    db: Session = Depends(get_db)
):
    """
    Verify email address

    Validates the verification token and marks email as verified
    """
    # Get customer ID from Redis
    customer_id = redis_client.get(f"verify:{request.token}")

    if not customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ungültiger oder abgelaufener Verifizierungslink"
        )

    # Get customer
    customer = db.query(Customer).filter(Customer.id == customer_id).first()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kunde nicht gefunden"
        )

    if customer.email_verified:
        return {"message": "E-Mail bereits verifiziert"}

    # Mark as verified
    customer.email_verified = True
    customer.email_verified_at = datetime.utcnow()

    db.commit()

    # Delete token from Redis
    redis_client.delete(f"verify:{request.token}")

    return {"message": "E-Mail erfolgreich verifiziert"}


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    User login

    Validates credentials and returns JWT token
    Works with new User model (platform admins, customer users)
    """
    # Get user by email
    user = db.query(User).filter(User.email == request.email).first()

    # Verify password
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ungültige Anmeldedaten"
        )

    # Check if account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ihr Konto wurde deaktiviert. Bitte kontaktieren Sie den Support."
        )

    # Update login tracking
    user.last_login_at = datetime.utcnow()
    user.login_count += 1
    user.failed_login_attempts = 0
    db.commit()

    # Get customer (if applicable)
    customer = None
    if user.customer_id:
        customer = db.query(Customer).filter(Customer.id == user.customer_id).first()

    # Create access token with user context
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "user_id": str(user.id),
            "email": user.email,
            "customer_id": str(user.customer_id) if user.customer_id else None,
            "role": user.role.value
        }
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.from_orm(user),
        customer=CustomerResponse.from_orm(customer) if customer else None
    )


class ForgotPasswordRequest(BaseModel):
    """Password reset request"""
    email: EmailStr


@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Request password reset

    Sends password reset email if customer exists
    """
    testing_mode = os.getenv("TESTING", "false").lower() == "true"

    customer = db.query(Customer).filter(Customer.contact_email == request.email).first()

    # Don't reveal if customer exists or not (security)
    if not customer:
        return {"message": "Falls ein Konto mit dieser E-Mail existiert, wurde eine E-Mail gesendet."}

    # Generate reset token
    token = secrets.token_urlsafe(32)

    # Store token in Redis (1 hour expiration)
    redis_client.setex(
        f"reset:{token}",
        timedelta(hours=1),
        str(customer.id)
    )

    if testing_mode:
        # Test mode: Return token in response
        return {
            "message": "Falls ein Konto mit dieser E-Mail existiert, wurde eine E-Mail gesendet.",
            "reset_token": token  # Only in test mode
        }

    # Production: Send password reset email
    # await EmailService.send_password_reset_email(...)

    return {"message": "Falls ein Konto mit dieser E-Mail existiert, wurde eine E-Mail gesendet."}


class ResetPasswordRequest(BaseModel):
    """Reset password request"""
    token: str
    new_password: str


@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Reset password

    Validates reset token and updates password
    """
    # Get customer ID from Redis
    customer_id = redis_client.get(f"reset:{request.token}")

    if not customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ungültiger oder abgelaufener Reset-Link"
        )

    # Get customer
    customer = db.query(Customer).filter(Customer.id == customer_id).first()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kunde nicht gefunden"
        )

    # Update password
    customer.password_hash = hash_password(request.new_password)
    db.commit()

    # Delete token from Redis
    redis_client.delete(f"reset:{request.token}")

    return {"message": "Passwort erfolgreich zurückgesetzt"}


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    token: str


@router.post("/refresh")
async def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh JWT token.

    Validates existing token and returns a new one with extended expiration.
    """
    from ..utils.security import create_access_token
    from jose import jwt

    try:
        # Decode token (without verification to allow expired tokens)
        payload = jwt.decode(
            request.token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"verify_exp": False}  # Allow expired tokens for refresh
        )

        customer_id = payload.get("sub")
        email = payload.get("email")

        if not customer_id or not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

        # Verify customer still exists and is active
        customer = db.query(Customer).filter(Customer.id == customer_id).first()

        if not customer or customer.status != "active":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account not found or inactive"
            )

        # Create new token
        new_token = create_access_token(data={
            "sub": str(customer.id),
            "email": customer.contact_email,
            "customer_id": str(customer.id),
            "role": "customer"
        })

        return {
            "access_token": new_token,
            "token_type": "bearer"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
