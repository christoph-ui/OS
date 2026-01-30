"""add onboarding status

Revision ID: 20260120_160000
Revises: d9c9cadef9b3
Create Date: 2026-01-20 16:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260120_160000'
down_revision = '20260119_110000'  # Updated to latest migration
branch_labels = None
depends_on = None


def upgrade():
    # Add onboarding status tracking columns to customers table
    op.add_column('customers', sa.Column('onboarding_status', sa.String(length=20), server_default='not_started', nullable=True))
    op.add_column('customers', sa.Column('onboarding_step', sa.String(length=50), nullable=True))
    op.add_column('customers', sa.Column('onboarding_data', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True))
    op.add_column('customers', sa.Column('onboarding_completed_at', sa.DateTime(timezone=True), nullable=True))

    # Update existing customers to have onboarding_status set
    op.execute("UPDATE customers SET onboarding_status = 'not_started' WHERE onboarding_status IS NULL")


def downgrade():
    # Remove onboarding status tracking columns
    op.drop_column('customers', 'onboarding_completed_at')
    op.drop_column('customers', 'onboarding_data')
    op.drop_column('customers', 'onboarding_step')
    op.drop_column('customers', 'onboarding_status')
