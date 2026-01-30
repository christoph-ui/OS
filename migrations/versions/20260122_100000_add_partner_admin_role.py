"""add partner admin role and partners table

Revision ID: 20260122_100000
Revises: 20260120_160000
Create Date: 2026-01-22 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260122_100000'
down_revision = '20260120_160000'
branch_labels = None
depends_on = None


def upgrade():
    # Step 1: Add 'partner_admin' to user_role enum (if not exists)
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_enum e
                JOIN pg_type t ON e.enumtypid = t.oid
                WHERE t.typname = 'user_role' AND e.enumlabel = 'partner_admin'
            ) THEN
                ALTER TYPE user_role ADD VALUE 'partner_admin';
            END IF;
        END $$;
    """)

    # Step 2: Create partners table (if not exists)
    op.execute("""
        CREATE TABLE IF NOT EXISTS partners (
            id UUID PRIMARY KEY,
            company_name VARCHAR(255) NOT NULL,
            contact_email VARCHAR(255) NOT NULL UNIQUE,
            contact_phone VARCHAR(50),
            street VARCHAR(255),
            city VARCHAR(100),
            postal_code VARCHAR(20),
            country VARCHAR(2) DEFAULT 'DE',
            vat_id VARCHAR(50),
            stripe_connect_account_id VARCHAR(255) UNIQUE,
            status VARCHAR(20) DEFAULT 'active',
            email_verified BOOLEAN DEFAULT false,
            email_verified_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
        );
    """)

    # Create indexes (if not exists)
    op.execute("CREATE INDEX IF NOT EXISTS ix_partners_contact_email ON partners(contact_email);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_partners_stripe_connect_account_id ON partners(stripe_connect_account_id);")


    # Step 3: Add partner_id to customers table
    op.add_column(
        'customers',
        sa.Column('partner_id', postgresql.UUID(as_uuid=True), nullable=True)
    )

    # Add foreign key constraint
    op.create_foreign_key(
        'fk_customers_partner_id',
        'customers',
        'partners',
        ['partner_id'],
        ['id'],
        ondelete='SET NULL'
    )

    # Create index
    op.create_index('ix_customers_partner_id', 'customers', ['partner_id'])

    # Step 4: Add partner_id to users table
    op.add_column(
        'users',
        sa.Column('partner_id', postgresql.UUID(as_uuid=True), nullable=True)
    )

    # Add foreign key constraint
    op.create_foreign_key(
        'fk_users_partner_id',
        'users',
        'partners',
        ['partner_id'],
        ['id'],
        ondelete='CASCADE'
    )

    # Create index
    op.create_index('ix_users_partner_id', 'users', ['partner_id'])


def downgrade():
    # Remove partner_id from users
    op.drop_index('ix_users_partner_id', 'users')
    op.drop_constraint('fk_users_partner_id', 'users', type_='foreignkey')
    op.drop_column('users', 'partner_id')

    # Remove partner_id from customers
    op.drop_index('ix_customers_partner_id', 'customers')
    op.drop_constraint('fk_customers_partner_id', 'customers', type_='foreignkey')
    op.drop_column('customers', 'partner_id')

    # Drop partners table
    op.drop_index('ix_partners_stripe_connect_account_id', 'partners')
    op.drop_index('ix_partners_contact_email', 'partners')
    op.drop_table('partners')

    # Note: Cannot remove value from enum in PostgreSQL easily
    # Would require recreating the enum type
