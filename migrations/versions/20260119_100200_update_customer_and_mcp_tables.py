"""update customer and mcp tables for user management

Revision ID: 20260119_100200
Revises: 20260119_100100
Create Date: 2026-01-19 10:02:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260119_100200'
down_revision = '20260119_100100'
branch_labels = None
depends_on = None


def upgrade():
    # Update customers table
    # Add primary_admin_id (will be populated by data migration)
    op.add_column('customers', sa.Column('primary_admin_id', postgresql.UUID(as_uuid=True), nullable=True))

    # Create foreign key (with post_update to avoid circular dependency)
    op.create_foreign_key(
        'fk_customers_primary_admin_id',
        'customers', 'users',
        ['primary_admin_id'], ['id'],
        ondelete='SET NULL'
    )

    # Update mcps table
    # Add developer_id for third-party MCPs
    op.add_column('mcps', sa.Column('developer_id', postgresql.UUID(as_uuid=True), nullable=True))

    # Add approval workflow columns
    op.add_column('mcps', sa.Column('approval_status', sa.String(20), server_default='pending'))
    op.add_column('mcps', sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('mcps', sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('mcps', sa.Column('approved_by_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('mcps', sa.Column('rejection_reason', sa.Text(), nullable=True))

    # Create indexes
    op.create_index('ix_mcps_developer_id', 'mcps', ['developer_id'])
    op.create_index('ix_mcps_approval_status', 'mcps', ['approval_status'])

    # Create foreign keys
    op.create_foreign_key(
        'fk_mcps_developer_id',
        'mcps', 'mcp_developers',
        ['developer_id'], ['id'],
        ondelete='CASCADE'
    )

    op.create_foreign_key(
        'fk_mcps_approved_by_id',
        'mcps', 'users',
        ['approved_by_id'], ['id'],
        ondelete='SET NULL'
    )

    # Set existing (first-party) MCPs to approved status
    op.execute("""
        UPDATE mcps
        SET approval_status = 'approved',
            approved_at = NOW()
        WHERE developer_id IS NULL
    """)


def downgrade():
    # Drop foreign keys and columns from mcps
    op.drop_constraint('fk_mcps_approved_by_id', 'mcps', type_='foreignkey')
    op.drop_constraint('fk_mcps_developer_id', 'mcps', type_='foreignkey')

    op.drop_index('ix_mcps_approval_status', 'mcps')
    op.drop_index('ix_mcps_developer_id', 'mcps')

    op.drop_column('mcps', 'rejection_reason')
    op.drop_column('mcps', 'approved_by_id')
    op.drop_column('mcps', 'approved_at')
    op.drop_column('mcps', 'submitted_at')
    op.drop_column('mcps', 'approval_status')
    op.drop_column('mcps', 'developer_id')

    # Drop foreign key and column from customers
    op.drop_constraint('fk_customers_primary_admin_id', 'customers', type_='foreignkey')
    op.drop_column('customers', 'primary_admin_id')
