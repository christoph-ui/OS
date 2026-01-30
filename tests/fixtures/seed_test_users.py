"""
Seed Test Users

Creates test users in the database for E2E testing.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from api.database import Base
from api.models.customer import Customer
from api.utils.security import hash_password


def seed_test_users(database_url: str = None):
    """
    Create test users in the database.

    Args:
        database_url: Database connection string
    """
    if database_url is None:
        database_url = os.getenv(
            "TEST_DATABASE_URL",
            "postgresql://0711:0711_dev_password@localhost:4005/0711_control"
        )

    # Create engine
    engine = create_engine(database_url)

    # Create tables
    Base.metadata.create_all(bind=engine)

    # Create session
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Test User 1: Basic customer
        test_user_1 = db.query(Customer).filter(
            Customer.contact_email == "test@test.0711.io"
        ).first()

        if not test_user_1:
            test_user_1 = Customer(
                company_name="Test Company",
                contact_email="test@test.0711.io",
                contact_name="Test User",
                password_hash=hash_password("TestPass123!"),
                tier="professional",
                status="active",
                email_verified=True,
                country="DE"  # ISO 2-letter code
            )
            db.add(test_user_1)

        # Test User 2: Another customer (for isolation testing)
        test_user_2 = db.query(Customer).filter(
            Customer.contact_email == "test2@test.0711.io"
        ).first()

        if not test_user_2:
            test_user_2 = Customer(
                company_name="Test Company 2",
                contact_email="test2@test.0711.io",
                contact_name="Test User 2",
                password_hash=hash_password("TestPass456!"),
                tier="business",
                status="active",
                email_verified=True,
                country="DE"  # ISO 2-letter code
            )
            db.add(test_user_2)

        # Admin User
        admin_user = db.query(Customer).filter(
            Customer.contact_email == "admin@test.0711.io"
        ).first()

        if not admin_user:
            admin_user = Customer(
                company_name="Admin Company",
                contact_email="admin@test.0711.io",
                contact_name="Admin User",
                password_hash=hash_password("AdminPass123!"),
                tier="enterprise",
                status="active",
                email_verified=True,
                country="DE"  # ISO 2-letter code
            )
            db.add(admin_user)

        db.commit()

        print("✅ Test users created successfully:")
        print(f"   • test@test.0711.io / TestPass123! (ID: {test_user_1.id})")
        print(f"   • test2@test.0711.io / TestPass456! (ID: {test_user_2.id})")
        print(f"   • admin@test.0711.io / AdminPass123! (ID: {admin_user.id})")

        return {
            "test_user_1": test_user_1,
            "test_user_2": test_user_2,
            "admin_user": admin_user
        }

    except Exception as e:
        db.rollback()
        print(f"❌ Error creating test users: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_test_users()
