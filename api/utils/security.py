"""
Security utilities: JWT tokens, password hashing, authentication
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token security
security = HTTPBearer()


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token

    Args:
        data: Payload to encode (e.g., {"sub": user_id})
        expires_delta: Optional expiration time

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expiration_minutes)

    to_encode.update({"exp": expire, "iat": datetime.utcnow()})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm
    )

    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT token

    Args:
        token: JWT token string

    Returns:
        Decoded payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


def get_current_customer_id(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> str:
    """
    Dependency to get current customer ID from JWT token

    Usage:
        @app.get("/me")
        def get_me(customer_id: str = Depends(get_current_customer_id)):
            ...
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    customer_id: Optional[str] = payload.get("sub")
    if customer_id is None:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials"
        )

    return customer_id


def get_current_admin_id(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> str:
    """
    Dependency to get current admin user ID from JWT token
    Also validates that the user has admin role
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    user_id: Optional[str] = payload.get("sub")
    role: Optional[str] = payload.get("role")

    if user_id is None or role not in ["admin", "platform_admin"]:
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    return user_id


def require_admin(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> None:
    """
    Dependency that validates admin access
    Raises 403 if not admin
    """
    get_current_admin_id(credentials)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
):
    """
    Dependency to get current User object from JWT token

    Returns full User model instance. Works with new User-based auth.

    Usage:
        @app.get("/profile")
        def get_profile(user: User = Depends(get_current_user)):
            return {"name": user.full_name}
    """
    from ..models.user import User

    token = credentials.credentials
    payload = decode_access_token(token)

    user_id: Optional[str] = payload.get("sub") or payload.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials"
        )

    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="User account is not active"
        )

    return user


def get_current_customer(
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Dependency to get current Customer object from authenticated user

    For customer users only (not platform admins or partner admins).

    Usage:
        @app.get("/company")
        def get_company(customer: Customer = Depends(get_current_customer)):
            return {"company": customer.company_name}
    """
    from ..models.customer import Customer
    from ..models.user import UserRole

    if user.role == UserRole.PLATFORM_ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Platform admins do not belong to a customer"
        )

    if user.role == UserRole.PARTNER_ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Partner admins do not belong to a customer. Use get_current_partner instead."
        )

    if not user.customer_id:
        raise HTTPException(
            status_code=400,
            detail="User does not belong to a customer"
        )

    customer = db.query(Customer).filter(Customer.id == user.customer_id).first()

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    return customer


def get_current_partner(
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Dependency to get current Partner object from authenticated user

    For partner admin users only.

    Usage:
        @app.get("/partner/dashboard")
        def get_dashboard(partner: Partner = Depends(get_current_partner)):
            return {"partner": partner.company_name}
    """
    from ..models.partner import Partner
    from ..models.user import UserRole

    if user.role != UserRole.PARTNER_ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Only partner admins can access partner resources"
        )

    if not user.partner_id:
        raise HTTPException(
            status_code=400,
            detail="User does not belong to a partner"
        )

    partner = db.query(Partner).filter(Partner.id == user.partner_id).first()

    if not partner:
        raise HTTPException(
            status_code=404,
            detail="Partner not found"
        )

    if not partner.is_active:
        raise HTTPException(
            status_code=403,
            detail="Partner account is not active"
        )

    return partner


def require_role(*allowed_roles: str):
    """
    Dependency factory for role-based access control

    Usage:
        @app.get("/admin/dashboard", dependencies=[Depends(require_role("platform_admin"))])
        async def admin_dashboard():
            ...

        @app.post("/billing", dependencies=[Depends(require_role("platform_admin", "customer_admin"))])
        async def update_billing():
            ...
    """
    from ..models.user import UserRole

    def role_checker(user = Depends(get_current_user)):
        if user.role.value not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
            )
        return user

    return role_checker


def require_permission(permission: str):
    """
    Dependency factory for permission-based access control

    Usage:
        @app.post("/billing/edit", dependencies=[Depends(require_permission("billing.edit"))])
        async def edit_billing():
            ...
    """
    def permission_checker(user = Depends(get_current_user)):
        if not user.has_permission(permission):
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Required permission: {permission}"
            )
        return user

    return permission_checker


def require_partner_admin():
    """
    Dependency that requires partner_admin role

    Usage:
        @app.get("/partners/customers", dependencies=[Depends(require_partner_admin())])
        async def list_partner_customers():
            ...
    """
    return require_role("partner_admin")
