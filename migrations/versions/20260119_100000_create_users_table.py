"""create users table with rbac

Revision ID: 20260119_100000
Revises: 20251220_034500
Create Date: 2026-01-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260119_100000'
down_revision = '20251220_034500'
branch_labels = None
depends_on = None


def upgrade():
    # Create user_role enum using raw SQL (IF NOT EXISTS)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE user_role AS ENUM ('platform_admin', 'customer_admin', 'customer_user');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create user_status enum using raw SQL (IF NOT EXISTS)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE user_status AS ENUM ('active', 'suspended', 'invited', 'inactive');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=True),
        sa.Column('email_verified', sa.Boolean(), default=False),
        sa.Column('email_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('role', sa.String(20), nullable=False, server_default='customer_user'),
        sa.Column('permissions', postgresql.JSONB(), default={}),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('login_count', sa.Integer(), default=0),
        sa.Column('failed_login_attempts', sa.Integer(), default=0),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('invited_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('invited_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('invitation_accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Create indexes
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_customer_id', 'users', ['customer_id'])
    op.create_index('ix_users_role', 'users', ['role'])

    # Create foreign key to customers
    op.create_foreign_key(
        'fk_users_customer_id',
        'users', 'customers',
        ['customer_id'], ['id'],
        ondelete='CASCADE'
    )

    # Create self-referencing foreign key for invited_by_id
    op.create_foreign_key(
        'fk_users_invited_by_id',
        'users', 'users',
        ['invited_by_id'], ['id'],
        ondelete='SET NULL'
    )


def downgrade():
    # Drop foreign keys
    op.drop_constraint('fk_users_invited_by_id', 'users', type_='foreignkey')
    op.drop_constraint('fk_users_customer_id', 'users', type_='foreignkey')

    # Drop indexes
    op.drop_index('ix_users_role', 'users')
    op.drop_index('ix_users_customer_id', 'users')
    op.drop_index('ix_users_email', 'users')

    # Drop table
    op.drop_table('users')

    # Drop enums
    op.execute('DROP TYPE user_role')
    op.execute('DROP TYPE user_status')
