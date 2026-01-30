"""Rename MCP to Connector

Revision ID: 20260130_150000
Revises: 61f593ecca3b
Create Date: 2026-01-30 15:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '20260130_150000'
down_revision: Union[str, None] = '61f593ecca3b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename tables
    op.rename_table('mcps', 'connectors')
    op.rename_table('mcp_installations', 'connections')
    op.rename_table('mcp_developers', 'connector_developers')
    
    # Rename columns in customers table
    op.alter_column('customers', 'enabled_mcps', new_column_name='enabled_connectors')
    op.alter_column('customers', 'connected_mcps', new_column_name='active_connections')
    
    # Rename columns in experts table
    op.alter_column('experts', 'mcp_expertise', new_column_name='connector_expertise')
    
    # Rename columns in engagements table
    op.alter_column('engagements', 'mcps_used', new_column_name='connectors_used')
    
    # Rename columns in tasks table
    op.alter_column('tasks', 'mcp_used', new_column_name='connector_used')
    
    # Rename columns in workflows table
    op.alter_column('workflows', 'required_mcps', new_column_name='required_connectors')
    
    # Rename columns in connections (formerly mcp_installations)
    op.alter_column('connections', 'mcp_id', new_column_name='connector_id')
    
    # Rename columns in connection_credentials
    op.alter_column('connection_credentials', 'mcp_installation_id', new_column_name='connection_id')
    op.alter_column('connection_credentials', 'mcp_id', new_column_name='connector_id')
    
    # Rename columns in workflow_step_logs
    op.alter_column('workflow_step_logs', 'mcp_name', new_column_name='connector_name')
    op.alter_column('workflow_step_logs', 'mcp_action', new_column_name='connector_action')
    op.alter_column('workflow_step_logs', 'mcp_response_time_ms', new_column_name='connector_response_time_ms')
    
    # Rename indexes (PostgreSQL syntax)
    op.execute('ALTER INDEX IF EXISTS ix_mcps_name RENAME TO ix_connectors_name')
    op.execute('ALTER INDEX IF EXISTS ix_mcps_developer_id RENAME TO ix_connectors_developer_id')
    op.execute('ALTER INDEX IF EXISTS ix_mcp_installations_customer_id RENAME TO ix_connections_customer_id')
    op.execute('ALTER INDEX IF EXISTS ix_mcp_installations_mcp_id RENAME TO ix_connections_connector_id')
    op.execute('ALTER INDEX IF EXISTS ix_mcp_installations_deployment_id RENAME TO ix_connections_deployment_id')
    op.execute('ALTER INDEX IF EXISTS ix_mcp_developers_user_id RENAME TO ix_connector_developers_user_id')
    op.execute('ALTER INDEX IF EXISTS ix_mcp_developers_email RENAME TO ix_connector_developers_email')
    op.execute('ALTER INDEX IF EXISTS ix_mcp_developers_stripe_account_id RENAME TO ix_connector_developers_stripe_account_id')
    op.execute('ALTER INDEX IF EXISTS ix_connection_credentials_mcp_installation_id RENAME TO ix_connection_credentials_connection_id')
    op.execute('ALTER INDEX IF EXISTS ix_connection_credentials_mcp_id RENAME TO ix_connection_credentials_connector_id')
    
    # Rename foreign key constraints (drop and recreate)
    op.drop_constraint('connections_mcp_id_fkey', 'connections', type_='foreignkey')
    op.create_foreign_key('connections_connector_id_fkey', 'connections', 'connectors', ['connector_id'], ['id'])
    
    op.drop_constraint('connection_credentials_mcp_installation_id_fkey', 'connection_credentials', type_='foreignkey')
    op.create_foreign_key('connection_credentials_connection_id_fkey', 'connection_credentials', 'connections', ['connection_id'], ['id'])
    
    op.drop_constraint('connection_credentials_mcp_id_fkey', 'connection_credentials', type_='foreignkey')
    op.create_foreign_key('connection_credentials_connector_id_fkey', 'connection_credentials', 'connectors', ['connector_id'], ['id'])


def downgrade() -> None:
    # Reverse all the renames
    op.rename_table('connectors', 'mcps')
    op.rename_table('connections', 'mcp_installations')
    op.rename_table('connector_developers', 'mcp_developers')
    
    op.alter_column('customers', 'enabled_connectors', new_column_name='enabled_mcps')
    op.alter_column('customers', 'active_connections', new_column_name='connected_mcps')
    op.alter_column('experts', 'connector_expertise', new_column_name='mcp_expertise')
    op.alter_column('engagements', 'connectors_used', new_column_name='mcps_used')
    op.alter_column('tasks', 'connector_used', new_column_name='mcp_used')
    op.alter_column('workflows', 'required_connectors', new_column_name='required_mcps')
    op.alter_column('mcp_installations', 'connector_id', new_column_name='mcp_id')
    op.alter_column('connection_credentials', 'connection_id', new_column_name='mcp_installation_id')
    op.alter_column('connection_credentials', 'connector_id', new_column_name='mcp_id')
    op.alter_column('workflow_step_logs', 'connector_name', new_column_name='mcp_name')
    op.alter_column('workflow_step_logs', 'connector_action', new_column_name='mcp_action')
    op.alter_column('workflow_step_logs', 'connector_response_time_ms', new_column_name='mcp_response_time_ms')
