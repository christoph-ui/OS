"""
Authentication Module

Provides JWT-based authentication and authorization.
"""

from .models import User, TokenData, UserCreate, UserLogin
from .jwt import create_access_token, verify_token, get_password_hash, verify_password
from .dependencies import get_current_user, get_current_active_user, require_auth

__all__ = [
    "User",
    "TokenData",
    "UserCreate",
    "UserLogin",
    "create_access_token",
    "verify_token",
    "get_password_hash",
    "verify_password",
    "get_current_user",
    "get_current_active_user",
    "require_auth",
]
