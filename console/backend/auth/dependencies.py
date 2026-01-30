"""
Authentication Dependencies

FastAPI dependencies for protecting routes.
"""

from typing import Optional
import logging

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .jwt import verify_token
from .models import TokenData, CustomerContext
from .store import get_user_by_id

logger = logging.getLogger(__name__)

# Bearer token security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[TokenData]:
    """
    Get current user from JWT token.

    Returns None if no token provided (for optional auth).
    Raises 401 if token is invalid.
    """
    if credentials is None:
        return None

    token = credentials.credentials
    token_data = verify_token(token)

    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token_data


async def get_current_active_user(
    token_data: Optional[TokenData] = Depends(get_current_user)
) -> TokenData:
    """
    Get current active user (required auth).

    Raises 401 if not authenticated.
    """
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Optionally check if user is still active in database
    # Skip user check if token has valid customer_id (allows Control Plane tokens)
    user = await get_user_by_id(token_data.user_id)
    if user and not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User inactive",
        )
    # If user not found in local store but token is valid, accept it (Control Plane token)

    return token_data


async def require_auth(
    token_data: TokenData = Depends(get_current_active_user)
) -> CustomerContext:
    """
    Require authentication and return customer context.

    Use this dependency on protected routes.

    Example:
        @router.get("/protected")
        async def protected_route(ctx: CustomerContext = Depends(require_auth)):
            # ctx.customer_id is available
            pass
    """
    user = await get_user_by_id(token_data.user_id)

    # Default permissions if user not in local store (Control Plane tokens)
    allowed_mcps = user.allowed_mcps if user else ["ctax", "law", "tender", "etim"]

    return CustomerContext(
        customer_id=token_data.customer_id,
        user_id=token_data.user_id,
        user_email=token_data.email,
        is_admin=token_data.is_admin,
        allowed_mcps=allowed_mcps
    )


async def require_admin(
    ctx: CustomerContext = Depends(require_auth)
) -> CustomerContext:
    """
    Require admin privileges.

    Raises 403 if user is not admin.
    """
    if not ctx.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return ctx


def get_customer_context(request: Request) -> Optional[CustomerContext]:
    """
    Get customer context from request state.

    For use in routes that set context via middleware.
    """
    return getattr(request.state, "customer_context", None)
