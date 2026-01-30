"""add_mcp_direction_and_connected_mcps

Revision ID: d9c9cadef9b3
Revises: 20260119_100300
Create Date: 2026-01-19 13:15:36.903673

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd9c9cadef9b3'
down_revision: Union[str, None] = '20260119_100300'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add direction field to mcps table
    op.add_column('mcps', sa.Column('direction', sa.String(length=20), nullable=True))

    # Set default value for existing records
    op.execute("UPDATE mcps SET direction = 'output' WHERE direction IS NULL")

    # Add connected_mcps field to customers table
    from sqlalchemy.dialects import postgresql
    op.add_column('customers', sa.Column('connected_mcps', postgresql.JSONB(), nullable=True))

    # Set default value for existing records
    op.execute("UPDATE customers SET connected_mcps = '{\"input\": [], \"output\": []}'::jsonb WHERE connected_mcps IS NULL")


def downgrade() -> None:
    # Remove connected_mcps from customers table
    op.drop_column('customers', 'connected_mcps')

    # Remove direction from mcps table
    op.drop_column('mcps', 'direction')
