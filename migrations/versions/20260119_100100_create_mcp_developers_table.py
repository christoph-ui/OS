"""create mcp_developers table

Revision ID: 20260119_100100
Revises: 20260119_100000
Create Date: 2026-01-19 10:01:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260119_100100'
down_revision = '20260119_100000'
branch_labels = None
depends_on = None


def upgrade():
    # Create mcp_developers table
    op.create_table(
        'mcp_developers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('company_name', sa.String(255), nullable=False),
        sa.Column('developer_name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('website', sa.String(500), nullable=True),
        sa.Column('github_url', sa.String(500), nullable=True),
        sa.Column('linkedin_url', sa.String(500), nullable=True),
        sa.Column('twitter_handle', sa.String(100), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('expertise_areas', postgresql.JSONB(), nullable=True),
        sa.Column('verified', sa.Boolean(), default=False),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verified_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('stripe_account_id', sa.String(255), nullable=True, unique=True),
        sa.Column('stripe_onboarding_complete', sa.Boolean(), default=False),
        sa.Column('revenue_share_percentage', sa.Integer(), default=70),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('total_mcps', sa.Integer(), default=0),
        sa.Column('published_mcps', sa.Integer(), default=0),
        sa.Column('total_installations', sa.Integer(), default=0),
        sa.Column('avg_rating', sa.DECIMAL(3, 2), default=0.0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('last_active_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Create indexes
    op.create_index('ix_mcp_developers_email', 'mcp_developers', ['email'])
    op.create_index('ix_mcp_developers_user_id', 'mcp_developers', ['user_id'])
    op.create_index('ix_mcp_developers_stripe_account_id', 'mcp_developers', ['stripe_account_id'])

    # Create foreign keys
    op.create_foreign_key(
        'fk_mcp_developers_user_id',
        'mcp_developers', 'users',
        ['user_id'], ['id'],
        ondelete='SET NULL'
    )

    op.create_foreign_key(
        'fk_mcp_developers_verified_by_id',
        'mcp_developers', 'users',
        ['verified_by_id'], ['id'],
        ondelete='SET NULL'
    )


def downgrade():
    # Drop foreign keys
    op.drop_constraint('fk_mcp_developers_verified_by_id', 'mcp_developers', type_='foreignkey')
    op.drop_constraint('fk_mcp_developers_user_id', 'mcp_developers', type_='foreignkey')

    # Drop indexes
    op.drop_index('ix_mcp_developers_stripe_account_id', 'mcp_developers')
    op.drop_index('ix_mcp_developers_user_id', 'mcp_developers')
    op.drop_index('ix_mcp_developers_email', 'mcp_developers')

    # Drop table
    op.drop_table('mcp_developers')
