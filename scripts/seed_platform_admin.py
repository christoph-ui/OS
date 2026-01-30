"""
Seed script to create initial platform administrator

Usage:
    python scripts/seed_platform_admin.py

Environment variables (optional):
    ADMIN_EMAIL - Admin email (default: admin@0711.io)
    ADMIN_PASSWORD - Admin password (default: randomly generated)
    ADMIN_FIRST_NAME - First name (default: Platform)
    ADMIN_LAST_NAME - Last name (default: Admin)
"""

import os
import sys
import uuid
import secrets
import string
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from api.database import SessionLocal
from api.models.user import User, UserRole, UserStatus
from api.utils.security import hash_password


def generate_random_password(length=16):
    """Generate a secure random password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password


def create_platform_admin(
    db: Session,
    email: str = None,
    password: str = None,
    first_name: str = "Platform",
    last_name: str = "Admin"
):
    """
    Create a platform administrator user

    Args:
        db: Database session
        email: Admin email (default: admin@0711.io)
        password: Admin password (default: randomly generated)
        first_name: First name
        last_name: Last name

    Returns:
        User object and plaintext password (if generated)
    """
    email = email or os.getenv("ADMIN_EMAIL", "admin@0711.io")
    password_was_generated = password is None

    if password is None:
        password = os.getenv("ADMIN_PASSWORD") or generate_random_password()

    # Check if admin already exists
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        print(f"✗ Admin user with email {email} already exists")
        return existing, None

    # Create platform admin
    admin = User(
        id=uuid.uuid4(),
        customer_id=None,  # Platform admins don't belong to a customer
        email=email,
        password_hash=hash_password(password),
        first_name=first_name,
        last_name=last_name,
        role=UserRole.PLATFORM_ADMIN,
        status=UserStatus.ACTIVE,
        permissions={"*": True},  # Wildcard permission (all access)
        email_verified=True,
        login_count=0,
        failed_login_attempts=0
    )

    db.add(admin)
    db.commit()
    db.refresh(admin)

    print(f"✓ Platform admin created successfully")
    print(f"  Email: {email}")
    print(f"  Name: {admin.full_name}")
    print(f"  Role: {admin.role.value}")

    if password_was_generated:
        return admin, password
    else:
        return admin, None


def main():
    """Main entry point"""
    print("=" * 60)
    print("0711 Platform - Create Platform Administrator")
    print("=" * 60)
    print()

    # Get configuration from environment
    email = os.getenv("ADMIN_EMAIL")
    password = os.getenv("ADMIN_PASSWORD")
    first_name = os.getenv("ADMIN_FIRST_NAME", "Platform")
    last_name = os.getenv("ADMIN_LAST_NAME", "Admin")

    # Create database session
    db = SessionLocal()

    try:
        # Create admin
        admin, generated_password = create_platform_admin(
            db=db,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        if admin and generated_password:
            print()
            print("=" * 60)
            print("⚠ IMPORTANT: Save these credentials ⚠")
            print("=" * 60)
            print(f"Email: {admin.email}")
            print(f"Password: {generated_password}")
            print()
            print("This password will NOT be shown again.")
            print("=" * 60)

    except Exception as e:
        print(f"✗ Error creating platform admin: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
