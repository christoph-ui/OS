"""add enabled_mcps to customer

Revision ID: 20251130_092000
Revises:
Create Date: 2025-11-30 09:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251130_092000'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add enabled_mcps JSONB column to customers table
    op.add_column('customers', sa.Column('enabled_mcps', postgresql.JSONB(), nullable=True))

    # Set default value for existing customers (empty dict)
    op.execute("UPDATE customers SET enabled_mcps = '{}'::jsonb WHERE enabled_mcps IS NULL")


def downgrade():
    # Remove enabled_mcps column
    op.drop_column('customers', 'enabled_mcps')
