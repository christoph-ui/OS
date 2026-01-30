"""
Create Eaton customer in database

This allows console users to subscribe to MCPs
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from api.database import SessionLocal
from api.models.customer import Customer
from api.models.user import User, UserRole
from api.utils.security import hash_password
import uuid

def create_eaton():
    db = SessionLocal()
    try:
        # Check if Eaton customer already exists
        existing_customer = db.query(Customer).filter(Customer.contact_email == "michael.weber@eaton.com").first()
        existing_user = db.query(User).filter(User.email == "michael.weber@eaton.com").first()

        if existing_customer and existing_user:
            print(f"✅ Eaton customer and user already exist")
            print(f"   Customer ID: {existing_customer.id}")
            print(f"   User ID: {existing_user.id}")
            return

        if existing_customer and not existing_user:
            print(f"✅ Customer exists, creating User...")
            customer = existing_customer
        else:

            # Create Customer
            customer = Customer(
                id=uuid.uuid4(),
                company_name="Eaton Corporation",
                company_type="AG",
                contact_name="Michael Weber",
                contact_email="michael.weber@eaton.com",
                contact_phone="+49 711 1234567",
                street="Hauptstraße 100",
                city="Stuttgart",
                postal_code="70173",
                country="DE",
                tier="enterprise",
                source="sales",
                status="active",
                enabled_mcps={},  # Will be populated via subscribe
                connected_mcps={"input": [], "output": []}
            )

            db.add(customer)
            db.flush()  # Get customer.id

        # Create User linked to Customer
        user = User(
            id=uuid.uuid4(),
            customer_id=customer.id,
            email="michael.weber@eaton.com",
            password_hash=hash_password("Eaton2025"),
            email_verified=True,
            first_name="Michael",
            last_name="Weber",
            role="CUSTOMER_ADMIN",  # Use string value, SQLAlchemy will convert to enum
            permissions={
                "mcps.subscribe": True,
                "mcps.connect": True,
                "billing.view": True
            },
            status="ACTIVE"  # Use string value
        )

        db.add(user)

        # Set primary admin
        customer.primary_admin_id = user.id

        db.commit()

        print("✅ Eaton customer created successfully!")
        print(f"\nCustomer Details:")
        print(f"  ID: {customer.id}")
        print(f"  Company: {customer.company_name}")
        print(f"  Email: {customer.contact_email}")
        print(f"  Tier: {customer.tier}")
        print(f"\nUser Details:")
        print(f"  ID: {user.id}")
        print(f"  Name: {user.full_name}")
        print(f"  Role: {user.role.value}")
        print(f"\nLogin Credentials:")
        print(f"  Email: michael.weber@eaton.com")
        print(f"  Password: Eaton2025")

    except Exception as e:
        print(f"❌ Error creating Eaton customer: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_eaton()
