"""
Authorization System

Manages permissions and access control
"""
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class Authorization:
    """
    Permission-based authorization

    Permissions are hierarchical:
    - platform_admin: Full access
    - customer_admin: Customer-level admin
    - customer_user: Limited access
    """

    # Permission definitions
    PERMISSIONS = {
        "platform_admin": [
            "*"  # All permissions
        ],
        "customer_admin": [
            "docker_access:read",
            "docker_access:write",
            "mcp_marketplace:read",
            "mcp_marketplace:install",
            "users:read",
            "users:invite",
            "users:manage",
            "data:read",
            "data:write",
            "billing:view"
        ],
        "customer_user": [
            "docker_access:read",
            "mcp_marketplace:read",
            "data:read"
        ]
    }

    @classmethod
    def has_permission(cls, user_role: str, permission: str) -> bool:
        """Check if role has permission"""

        role_permissions = cls.PERMISSIONS.get(user_role, [])

        # Admin has all permissions
        if "*" in role_permissions:
            return True

        # Check exact match
        if permission in role_permissions:
            return True

        # Check wildcard match (e.g., "data:*" matches "data:read")
        permission_parts = permission.split(":")
        if len(permission_parts) == 2:
            wildcard = f"{permission_parts[0]}:*"
            if wildcard in role_permissions:
                return True

        return False

    @classmethod
    def check_permission(cls, user: Dict, permission: str):
        """
        Check permission and raise exception if not allowed

        Args:
            user: User dict with 'role' field
            permission: Permission string (e.g., 'data:write')

        Raises:
            PermissionError: If user doesn't have permission
        """
        if not cls.has_permission(user["role"], permission):
            raise PermissionError(
                f"User {user['email']} (role: {user['role']}) "
                f"does not have permission: {permission}"
            )
