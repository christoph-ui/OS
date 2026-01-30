"""add_connection_credentials_and_extend_mcp_model

Revision ID: 61f593ecca3b
Revises: 20260122_100000
Create Date: 2026-01-23 04:23:19.110332

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '61f593ecca3b'
down_revision: Union[str, None] = '20260122_100000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create connection_credentials table
    op.create_table(
        'connection_credentials',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('customers.id'), nullable=False, index=True),
        sa.Column('mcp_installation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mcp_installations.id'), nullable=False, index=True),
        sa.Column('mcp_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mcps.id'), nullable=False, index=True),

        # Connection type
        sa.Column('connection_type', sa.String(50), nullable=False),

        # Encrypted credentials
        sa.Column('encrypted_credentials', sa.Text, nullable=False),

        # OAuth-specific fields
        sa.Column('oauth_provider', sa.String(100)),
        sa.Column('oauth_scopes', postgresql.JSONB),
        sa.Column('token_expires_at', sa.DateTime(timezone=True)),

        # Connection metadata
        sa.Column('connection_name', sa.String(255)),
        sa.Column('connection_metadata', postgresql.JSONB),

        # Status
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('health_status', sa.String(20), default='unknown'),
        sa.Column('last_health_check', sa.DateTime(timezone=True)),
        sa.Column('last_successful_use', sa.DateTime(timezone=True)),

        # Error tracking
        sa.Column('error_count', sa.Integer, default=0),
        sa.Column('last_error_message', sa.Text),
        sa.Column('last_error_at', sa.DateTime(timezone=True)),

        # Usage tracking
        sa.Column('total_api_calls', sa.Integer, default=0),

        # Security
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('user_agent', sa.String(500)),

        # Rotation tracking
        sa.Column('last_rotated_at', sa.DateTime(timezone=True)),
        sa.Column('rotation_interval_days', sa.Integer),

        # Compliance
        sa.Column('consent_given', sa.Boolean, default=True),
        sa.Column('consent_at', sa.DateTime(timezone=True)),
        sa.Column('data_residency', sa.String(50)),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True)),
        sa.Column('revoked_at', sa.DateTime(timezone=True))
    )

    # Add indexes
    op.create_index('ix_connection_credentials_customer_id', 'connection_credentials', ['customer_id'])
    op.create_index('ix_connection_credentials_mcp_id', 'connection_credentials', ['mcp_id'])
    op.create_index('ix_connection_credentials_status', 'connection_credentials', ['status'])

    # Extend mcps table with connection configuration
    op.add_column('mcps', sa.Column('connection_type', sa.String(50)))
    op.add_column('mcps', sa.Column('oauth_config', postgresql.JSONB))
    op.add_column('mcps', sa.Column('api_docs_url', sa.String(500)))
    op.add_column('mcps', sa.Column('setup_instructions', sa.Text))
    op.add_column('mcps', sa.Column('connection_test_endpoint', sa.String(500)))


def downgrade() -> None:
    # Remove columns from mcps table
    op.drop_column('mcps', 'connection_test_endpoint')
    op.drop_column('mcps', 'setup_instructions')
    op.drop_column('mcps', 'api_docs_url')
    op.drop_column('mcps', 'oauth_config')
    op.drop_column('mcps', 'connection_type')

    # Drop indexes
    op.drop_index('ix_connection_credentials_status', 'connection_credentials')
    op.drop_index('ix_connection_credentials_mcp_id', 'connection_credentials')
    op.drop_index('ix_connection_credentials_customer_id', 'connection_credentials')

    # Drop connection_credentials table
    op.drop_table('connection_credentials')
