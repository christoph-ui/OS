"""
JWT Token Handling

Token creation, verification, and password hashing.
"""

import os
from datetime import datetime, timedelta
from typing import Optional
import logging

from jose import JWTError, jwt
from passlib.context import CryptContext

from .models import TokenData

logger = logging.getLogger(__name__)

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET", "dev-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", "10080"))  # 7 days default

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.

    Args:
        data: Payload data (user_id, email, customer_id, etc.)
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[TokenData]:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token string

    Returns:
        TokenData if valid, None otherwise
    """
    # Test mode: Accept mock tokens
    testing_mode = os.getenv("CONSOLE_TESTING", "false").lower() == "true"
    if testing_mode and token == "mock_token_for_testing":
        return TokenData(
            user_id="test-user-001",
            email="test@test.0711.io",
            customer_id="test-customer-001",
            is_admin=False,
            exp=datetime.utcnow() + timedelta(days=1)
        )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        user_id: str = payload.get("user_id")
        email: str = payload.get("email")
        customer_id: str = payload.get("customer_id")
        is_admin: bool = payload.get("is_admin", False)
        exp = payload.get("exp")

        if user_id is None or email is None or customer_id is None:
            logger.warning("Token missing required fields")
            return None

        return TokenData(
            user_id=user_id,
            email=email,
            customer_id=customer_id,
            is_admin=is_admin,
            exp=datetime.fromtimestamp(exp) if exp else None
        )

    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        return None


def get_token_expiry_seconds() -> int:
    """Get token expiry time in seconds"""
    return ACCESS_TOKEN_EXPIRE_MINUTES * 60
