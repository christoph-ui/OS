"""add medusa registrations table

Revision ID: medusa_registrations_001
Revises: 20251130_120000_add_expert_network_tables
Create Date: 2025-12-20 03:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251220_034500'
down_revision = '20251130_120000'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'medusa_registrations',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=False),
        sa.Column('company', sa.String(), nullable=True),
        sa.Column('phone', sa.String(), nullable=False),
        sa.Column('address', sa.String(), nullable=False),
        sa.Column('city', sa.String(), nullable=False),
        sa.Column('postal_code', sa.String(), nullable=False),
        sa.Column('country', sa.String(), nullable=False),
        sa.Column('download_count', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # Create index on email for faster lookups
    op.create_index('idx_medusa_registrations_email', 'medusa_registrations', ['email'])
    op.create_index('idx_medusa_registrations_created_at', 'medusa_registrations', ['created_at'])


def downgrade():
    op.drop_index('idx_medusa_registrations_created_at')
    op.drop_index('idx_medusa_registrations_email')
    op.drop_table('medusa_registrations')
