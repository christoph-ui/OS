"""create workflows tables and marketplace

Revision ID: 20260119_110000
Revises: 20260119_100300
Create Date: 2026-01-19 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260119_110000'
down_revision = 'd9c9cadef9b3'  # Depends on MCP direction migration
branch_labels = None
depends_on = None


def upgrade():
    # Create workflows table
    op.create_table(
        'workflows',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('developer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('display_name', sa.String(255), nullable=False),
        sa.Column('version', sa.String(50), default='1.0.0'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('subcategory', sa.String(100), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('icon', sa.String(10), default='🔄'),
        sa.Column('icon_color', sa.String(50), default='purple'),
        sa.Column('required_mcps', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('estimated_duration_minutes', sa.Integer(), nullable=True),
        sa.Column('complexity_level', sa.String(20), nullable=True),
        sa.Column('featured', sa.Boolean(), default=False),
        sa.Column('verified', sa.Boolean(), default=False),
        sa.Column('pricing_model', sa.String(50), default='free'),
        sa.Column('price_per_month_cents', sa.Integer(), nullable=True),
        sa.Column('price_per_execution_cents', sa.Integer(), nullable=True),
        sa.Column('install_count', sa.Integer(), default=0),
        sa.Column('active_subscriptions', sa.Integer(), default=0),
        sa.Column('total_executions', sa.Integer(), default=0),
        sa.Column('rating', sa.DECIMAL(3, 2), default=0.0),
        sa.Column('review_count', sa.Integer(), default=0),
        sa.Column('avg_execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('success_rate', sa.DECIMAL(5, 2), default=100.0),
        sa.Column('approval_status', sa.String(20), default='pending'),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approved_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), default='active'),
        sa.Column('published', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Create indexes for workflows
    op.create_index('ix_workflows_name', 'workflows', ['name'])
    op.create_index('ix_workflows_developer_id', 'workflows', ['developer_id'])
    op.create_index('ix_workflows_category', 'workflows', ['category'])
    op.create_index('ix_workflows_approval_status', 'workflows', ['approval_status'])

    # Create foreign keys for workflows
    op.create_foreign_key(
        'fk_workflows_developer_id',
        'workflows', 'mcp_developers',
        ['developer_id'], ['id'],
        ondelete='CASCADE'
    )

    op.create_foreign_key(
        'fk_workflows_approved_by_id',
        'workflows', 'users',
        ['approved_by_id'], ['id'],
        ondelete='SET NULL'
    )

    # Create workflow_definitions table
    op.create_table(
        'workflow_definitions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version', sa.String(50), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('definition', postgresql.JSONB(), nullable=False),
        sa.Column('changelog', sa.Text(), nullable=True),
        sa.Column('breaking_changes', sa.Boolean(), default=False),
        sa.Column('validated', sa.Boolean(), default=False),
        sa.Column('validation_errors', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=True),
    )

    op.create_index('ix_workflow_definitions_workflow_id', 'workflow_definitions', ['workflow_id'])
    op.create_index('ix_workflow_definitions_is_active', 'workflow_definitions', ['is_active'])

    op.create_foreign_key(
        'fk_workflow_definitions_workflow_id',
        'workflow_definitions', 'workflows',
        ['workflow_id'], ['id'],
        ondelete='CASCADE'
    )

    op.create_foreign_key(
        'fk_workflow_definitions_created_by_id',
        'workflow_definitions', 'users',
        ['created_by_id'], ['id'],
        ondelete='SET NULL'
    )

    # Create workflow_subscriptions table
    op.create_table(
        'workflow_subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('enabled', sa.Boolean(), default=True),
        sa.Column('status', sa.String(20), default='active'),
        sa.Column('config', postgresql.JSONB(), default={}),
        sa.Column('schedule_enabled', sa.Boolean(), default=False),
        sa.Column('schedule_cron', sa.String(100), nullable=True),
        sa.Column('last_scheduled_run', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_scheduled_run', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_executions', sa.Integer(), default=0),
        sa.Column('successful_executions', sa.Integer(), default=0),
        sa.Column('failed_executions', sa.Integer(), default=0),
        sa.Column('last_execution_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('avg_execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('total_cost_cents', sa.Integer(), default=0),
        sa.Column('subscribed_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('unsubscribed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_index('ix_workflow_subscriptions_customer_id', 'workflow_subscriptions', ['customer_id'])
    op.create_index('ix_workflow_subscriptions_workflow_id', 'workflow_subscriptions', ['workflow_id'])

    op.create_foreign_key(
        'fk_workflow_subscriptions_customer_id',
        'workflow_subscriptions', 'customers',
        ['customer_id'], ['id'],
        ondelete='CASCADE'
    )

    op.create_foreign_key(
        'fk_workflow_subscriptions_workflow_id',
        'workflow_subscriptions', 'workflows',
        ['workflow_id'], ['id'],
        ondelete='CASCADE'
    )

    # Create workflow_executions table
    op.create_table(
        'workflow_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('subscription_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('triggered_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('current_step', sa.String(100), nullable=True),
        sa.Column('current_step_index', sa.Integer(), default=0),
        sa.Column('input_data', postgresql.JSONB(), nullable=True),
        sa.Column('output_data', postgresql.JSONB(), nullable=True),
        sa.Column('state_snapshot', postgresql.JSONB(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_step', sa.String(100), nullable=True),
        sa.Column('retry_count', sa.Integer(), default=0),
        sa.Column('max_retries', sa.Integer(), default=3),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('steps_completed', sa.Integer(), default=0),
        sa.Column('steps_failed', sa.Integer(), default=0),
        sa.Column('steps_skipped', sa.Integer(), default=0),
        sa.Column('cost_cents', sa.Integer(), default=0),
        sa.Column('trigger_type', sa.String(50), default='manual'),
        sa.Column('trigger_metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_index('ix_workflow_executions_customer_id', 'workflow_executions', ['customer_id'])
    op.create_index('ix_workflow_executions_workflow_id', 'workflow_executions', ['workflow_id'])
    op.create_index('ix_workflow_executions_status', 'workflow_executions', ['status'])

    op.create_foreign_key(
        'fk_workflow_executions_customer_id',
        'workflow_executions', 'customers',
        ['customer_id'], ['id'],
        ondelete='CASCADE'
    )

    op.create_foreign_key(
        'fk_workflow_executions_workflow_id',
        'workflow_executions', 'workflows',
        ['workflow_id'], ['id'],
        ondelete='CASCADE'
    )

    op.create_foreign_key(
        'fk_workflow_executions_subscription_id',
        'workflow_executions', 'workflow_subscriptions',
        ['subscription_id'], ['id'],
        ondelete='SET NULL'
    )

    op.create_foreign_key(
        'fk_workflow_executions_triggered_by_user_id',
        'workflow_executions', 'users',
        ['triggered_by_user_id'], ['id'],
        ondelete='SET NULL'
    )

    # Create workflow_step_logs table
    op.create_table(
        'workflow_step_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('execution_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('step_index', sa.Integer(), nullable=False),
        sa.Column('step_id', sa.String(100), nullable=False),
        sa.Column('step_name', sa.String(255), nullable=True),
        sa.Column('mcp_name', sa.String(100), nullable=True),
        sa.Column('mcp_action', sa.String(100), nullable=True),
        sa.Column('input_data', postgresql.JSONB(), nullable=True),
        sa.Column('output_data', postgresql.JSONB(), nullable=True),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_attempt', sa.Integer(), default=0),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('mcp_response_time_ms', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index('ix_workflow_step_logs_execution_id', 'workflow_step_logs', ['execution_id'])
    op.create_index('ix_workflow_step_logs_step_index', 'workflow_step_logs', ['step_index'])

    op.create_foreign_key(
        'fk_workflow_step_logs_execution_id',
        'workflow_step_logs', 'workflow_executions',
        ['execution_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade():
    # Drop tables in reverse order
    op.drop_table('workflow_step_logs')
    op.drop_table('workflow_executions')
    op.drop_table('workflow_subscriptions')
    op.drop_table('workflow_definitions')
    op.drop_table('workflows')
