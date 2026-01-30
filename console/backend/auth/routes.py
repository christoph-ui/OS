"""
Authentication Routes

Login, register, and user management endpoints.
"""

from datetime import datetime
import logging

from fastapi import APIRouter, HTTPException, status, Depends

from .models import User, UserCreate, UserLogin, Token, CustomerContext
from .jwt import create_access_token, get_token_expiry_seconds
from .store import create_user, authenticate_user, get_user_by_id
from .dependencies import require_auth, require_admin

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_create: UserCreate):
    """
    Register a new user.

    Creates a new user account and returns an access token.

    Example:
        POST /api/auth/register
        {
            "email": "user@example.com",
            "name": "John Doe",
            "customer_id": "acme_corp",
            "password": "securepassword123"
        }
    """
    try:
        user = await create_user(user_create)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Create access token
    access_token = create_access_token(
        data={
            "user_id": user.id,
            "email": user.email,
            "customer_id": user.customer_id,
            "is_admin": user.is_admin
        }
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=get_token_expiry_seconds(),
        user=user
    )


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """
    Login with email and password.

    Returns an access token on successful authentication.

    Example:
        POST /api/auth/login
        {
            "email": "user@example.com",
            "password": "securepassword123"
        }
    """
    user = await authenticate_user(credentials.email, credentials.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )

    # Create access token
    access_token = create_access_token(
        data={
            "user_id": user.id,
            "email": user.email,
            "customer_id": user.customer_id,
            "is_admin": user.is_admin
        }
    )

    logger.info(f"User logged in: {user.email}")

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=get_token_expiry_seconds(),
        user=user
    )


@router.get("/me", response_model=User)
async def get_current_user_info(ctx: CustomerContext = Depends(require_auth)):
    """
    Get current user information.

    Requires authentication.
    """
    user = await get_user_by_id(ctx.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.get("/context")
async def get_context(ctx: CustomerContext = Depends(require_auth)):
    """
    Get current customer context.

    Returns the customer context including:
    - customer_id (for data isolation)
    - user_id
    - allowed_mcps
    """
    return {
        "customer_id": ctx.customer_id,
        "user_id": ctx.user_id,
        "user_email": ctx.user_email,
        "is_admin": ctx.is_admin,
        "allowed_mcps": ctx.allowed_mcps
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(ctx: CustomerContext = Depends(require_auth)):
    """
    Refresh access token.

    Returns a new access token with extended expiry.
    """
    user = await get_user_by_id(ctx.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Create new access token
    access_token = create_access_token(
        data={
            "user_id": user.id,
            "email": user.email,
            "customer_id": user.customer_id,
            "is_admin": user.is_admin
        }
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=get_token_expiry_seconds(),
        user=user
    )
