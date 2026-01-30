"""
User model
Represents individual users (platform admins, customer admins, customer users)
Enables multi-tenant user management with RBAC
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, func, Enum as SQLEnum, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
import enum

from ..database import Base


class UserRole(str, enum.Enum):
    """User role enumeration"""
    PLATFORM_ADMIN = "platform_admin"  # 0711 platform administrators
    PARTNER_ADMIN = "partner_admin"    # Partner/agency administrators (manage multiple customers)
    CUSTOMER_ADMIN = "customer_admin"  # Customer's primary administrator
    CUSTOMER_USER = "customer_user"    # Regular customer employee


class UserStatus(str, enum.Enum):
    """User status enumeration"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    INVITED = "invited"  # User invited but hasn't set password yet
    INACTIVE = "inactive"


class User(Base):
    """User model - individual users with role-based access"""

    __tablename__ = "users"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key to customer (nullable for platform admins and partner admins)
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=True,  # Null for platform admins and partner admins
        index=True
    )

    # Foreign key to partner (only for partner admins)
    partner_id = Column(
        UUID(as_uuid=True),
        ForeignKey("partners.id", ondelete="CASCADE"),
        nullable=True,  # Only set for partner_admin role
        index=True
    )

    # Authentication
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255))  # Null until user sets password (invited users)
    email_verified = Column(Boolean, default=False)
    email_verified_at = Column(DateTime(timezone=True))

    # Personal information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)

    # Role and permissions
    role = Column(
        SQLEnum(
            UserRole,
            name="user_role",
            create_type=False,
            values_callable=lambda x: [e.value for e in x],  # Force use of .value (lowercase)
        ),
        nullable=False,
        default=UserRole.CUSTOMER_USER
    )

    # Granular permissions (JSONB for flexibility)
    # Example: {"billing.view": true, "billing.edit": false, "users.invite": true}
    # Platform admins can have {"*": true} for all permissions
    permissions = Column(JSONB, default={})

    # Status
    status = Column(
        SQLEnum(
            UserStatus,
            name="user_status",
            create_type=False,
            values_callable=lambda x: [e.value for e in x],  # Force use of .value (lowercase)
        ),
        nullable=False,
        default=UserStatus.ACTIVE
    )

    # Security
    last_login_at = Column(DateTime(timezone=True))
    login_count = Column(Integer, default=0)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True))  # Account lockout

    # Invitation tracking
    invited_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    invited_at = Column(DateTime(timezone=True))
    invitation_accepted_at = Column(DateTime(timezone=True))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))  # Soft delete

    # Relationships
    customer = relationship("Customer", back_populates="users", foreign_keys=[customer_id])
    partner = relationship("Partner", back_populates="users", foreign_keys=[partner_id])
    invited_by = relationship("User", remote_side=[id], foreign_keys=[invited_by_id])

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"

    @property
    def full_name(self) -> str:
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}"

    @property
    def is_platform_admin(self) -> bool:
        """Check if user is a platform administrator"""
        return self.role == UserRole.PLATFORM_ADMIN

    @property
    def is_partner_admin(self) -> bool:
        """Check if user is a partner administrator"""
        return self.role == UserRole.PARTNER_ADMIN

    @property
    def is_customer_admin(self) -> bool:
        """Check if user is a customer administrator"""
        return self.role == UserRole.CUSTOMER_ADMIN

    @property
    def is_active(self) -> bool:
        """Check if user account is active"""
        return self.status == UserStatus.ACTIVE and self.deleted_at is None

    def has_permission(self, permission: str) -> bool:
        """
        Check if user has a specific permission

        Args:
            permission: Permission string (e.g., "billing.edit", "users.invite")

        Returns:
            True if user has permission
        """
        if not self.permissions:
            return False

        # Platform admins with wildcard permission
        if self.permissions.get("*") is True:
            return True

        # Check specific permission
        return self.permissions.get(permission, False) is True

    def grant_permission(self, permission: str):
        """Grant a permission to the user"""
        if not self.permissions:
            self.permissions = {}
        self.permissions[permission] = True

    def revoke_permission(self, permission: str):
        """Revoke a permission from the user"""
        if self.permissions and permission in self.permissions:
            self.permissions[permission] = False
