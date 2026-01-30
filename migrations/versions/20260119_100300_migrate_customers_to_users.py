"""migrate existing customers to users table

Revision ID: 20260119_100300
Revises: 20260119_100200
Create Date: 2026-01-19 10:03:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '20260119_100300'
down_revision = '20260119_100200'
branch_labels = None
depends_on = None


def upgrade():
    """
    Migrate existing customers to users table.

    Creates one User (customer_admin) for each Customer.
    """
    conn = op.get_bind()

    # Get all existing customers
    customers = conn.execute(sa.text("""
        SELECT id, contact_name, contact_email, password_hash, email_verified, email_verified_at
        FROM customers
        WHERE contact_email IS NOT NULL
    """)).fetchall()

    for customer in customers:
        customer_id, contact_name, email, password_hash, email_verified, email_verified_at = customer

        # Split name into first_name and last_name (best effort)
        name_parts = contact_name.strip().split(' ', 1) if contact_name else ['', '']
        first_name = name_parts[0] or 'Admin'
        last_name = name_parts[1] if len(name_parts) > 1 else ''

        # Generate user ID
        user_id = str(uuid.uuid4())

        # Create user as customer_admin
        conn.execute(sa.text("""
            INSERT INTO users (
                id, customer_id, email, password_hash, email_verified, email_verified_at,
                first_name, last_name, role, status, permissions, login_count,
                failed_login_attempts, created_at, updated_at
            ) VALUES (
                :user_id, :customer_id, :email, :password_hash, :email_verified, :email_verified_at,
                :first_name, :last_name, 'customer_admin', 'active', '{}'::jsonb, 0,
                0, NOW(), NOW()
            )
        """), {
            'user_id': user_id,
            'customer_id': str(customer_id),
            'email': email,
            'password_hash': password_hash,
            'email_verified': email_verified or False,
            'email_verified_at': email_verified_at,
            'first_name': first_name,
            'last_name': last_name
        })

        # Set this user as primary_admin for the customer
        conn.execute(sa.text("""
            UPDATE customers
            SET primary_admin_id = :user_id
            WHERE id = :customer_id
        """), {'user_id': user_id, 'customer_id': str(customer_id)})


def downgrade():
    """
    Remove migrated users.

    This deletes all users that were created from customers (customer_admin role).
    """
    conn = op.get_bind()

    # Clear primary_admin_id from customers
    conn.execute(sa.text("""
        UPDATE customers
        SET primary_admin_id = NULL
    """))

    # Delete all customer users (not platform admins)
    conn.execute(sa.text("""
        DELETE FROM users
        WHERE customer_id IS NOT NULL
    """))
