"""add expert network tables

Revision ID: 20251130_120000
Revises: 20251130_092000
Create Date: 2025-11-30 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '20251130_120000'
down_revision = '20251130_092000'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ========================================================================
    # EXPERTS TABLE
    # ========================================================================
    op.create_table(
        'experts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('headline', sa.String(255), nullable=False),
        sa.Column('bio', sa.Text, nullable=True),
        sa.Column('linkedin_url', sa.String(500), nullable=True),

        # Capacity
        sa.Column('max_clients', sa.Integer, default=10),
        sa.Column('current_clients', sa.Integer, default=0),
        sa.Column('availability_status', sa.String(50), default='available'),

        # Pricing
        sa.Column('hourly_rate_min', sa.Integer, nullable=True),
        sa.Column('hourly_rate_max', sa.Integer, nullable=True),

        # Performance metrics
        sa.Column('avg_response_time_hours', sa.Numeric(5, 2), nullable=True),
        sa.Column('rating', sa.Numeric(3, 2), default=0),
        sa.Column('total_reviews', sa.Integer, default=0),
        sa.Column('total_tasks_completed', sa.Integer, default=0),

        # Arrays
        sa.Column('language_skills', postgresql.ARRAY(sa.String(50)), default=[]),
        sa.Column('industry_experience', postgresql.ARRAY(sa.String(100)), default=[]),
        sa.Column('tool_proficiencies', postgresql.ARRAY(sa.String(100)), default=[]),

        # Verification & banking
        sa.Column('tax_id', sa.String(100), nullable=True),
        sa.Column('iban', sa.String(100), nullable=True),
        sa.Column('bic', sa.String(50), nullable=True),
        sa.Column('stripe_connect_account_id', sa.String(100), nullable=True),

        # Status
        sa.Column('status', sa.String(50), default='pending'),  # pending, approved, rejected, paused
        sa.Column('quality_tier', sa.String(50), default='standard'),  # platinum, gold, silver, standard, probation
        sa.Column('approved_at', sa.DateTime, nullable=True),
        sa.Column('years_experience', sa.Integer, default=0),

        # Timestamps
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )

    # ========================================================================
    # EXPERT MCPS (Many-to-Many with proficiency levels)
    # ========================================================================
    op.create_table(
        'expert_mcps',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('expert_id', sa.String(36), sa.ForeignKey('experts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('mcp_id', sa.String(50), nullable=False),  # CTAX, FPA, LEGAL, etc.
        sa.Column('proficiency_level', sa.String(50), nullable=False),  # beginner, intermediate, expert
        sa.Column('certification_earned_at', sa.DateTime, nullable=True),
        sa.Column('tasks_completed', sa.Integer, default=0),
        sa.Column('ai_agreement_rate', sa.Numeric(5, 2), nullable=True),  # % expert agrees with AI
        sa.Column('avg_confidence_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
    )

    op.create_index('idx_expert_mcps_expert_id', 'expert_mcps', ['expert_id'])
    op.create_index('idx_expert_mcps_mcp_id', 'expert_mcps', ['mcp_id'])

    # ========================================================================
    # EXPERT CERTIFICATIONS
    # ========================================================================
    op.create_table(
        'expert_certifications',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('expert_id', sa.String(36), sa.ForeignKey('experts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('mcp_id', sa.String(50), nullable=True),  # Which MCP this cert applies to
        sa.Column('certification_name', sa.String(255), nullable=False),
        sa.Column('certification_type', sa.String(100), nullable=False),  # professional, platform, education
        sa.Column('file_url', sa.String(500), nullable=True),  # S3/MinIO path
        sa.Column('issuer', sa.String(255), nullable=True),
        sa.Column('verified_at', sa.DateTime, nullable=True),
        sa.Column('verified_by', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('expires_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
    )

    op.create_index('idx_expert_certifications_expert_id', 'expert_certifications', ['expert_id'])

    # ========================================================================
    # EXPERT-CLIENT ENGAGEMENTS
    # ========================================================================
    op.create_table(
        'expert_engagements',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('expert_id', sa.String(36), sa.ForeignKey('experts.id'), nullable=False),
        sa.Column('customer_id', sa.String(36), sa.ForeignKey('customers.id'), nullable=False),

        # MCPs covered by this engagement
        sa.Column('mcp_ids', postgresql.ARRAY(sa.String(50)), default=[]),

        # Pricing
        sa.Column('monthly_rate', sa.Integer, nullable=False),  # Total monthly fee
        sa.Column('expert_earnings', sa.Integer, nullable=False),  # 90% of monthly_rate
        sa.Column('platform_fee', sa.Integer, nullable=False),  # 10% of monthly_rate

        # Status
        sa.Column('status', sa.String(50), default='active'),  # active, paused, ended
        sa.Column('start_date', sa.Date, nullable=False),
        sa.Column('end_date', sa.Date, nullable=True),

        # Performance metrics
        sa.Column('health_score', sa.Integer, default=100),  # 0-100
        sa.Column('ai_automation_rate', sa.Numeric(5, 2), default=0),
        sa.Column('tasks_completed', sa.Integer, default=0),
        sa.Column('avg_task_completion_hours', sa.Numeric(6, 2), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_index('idx_engagements_expert_id', 'expert_engagements', ['expert_id'])
    op.create_index('idx_engagements_customer_id', 'expert_engagements', ['customer_id'])
    op.create_index('idx_engagements_status', 'expert_engagements', ['status'])

    # ========================================================================
    # EXPERT APPLICATIONS (before approval)
    # ========================================================================
    op.create_table(
        'expert_applications',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False),

        # Application data stored as JSON
        sa.Column('application_data', postgresql.JSONB, nullable=False),

        # Review status
        sa.Column('status', sa.String(50), default='submitted'),  # submitted, under_review, approved, rejected
        sa.Column('submitted_at', sa.DateTime, default=sa.func.now()),
        sa.Column('reviewed_by', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('reviewed_at', sa.DateTime, nullable=True),
        sa.Column('rejection_reason', sa.Text, nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
    )

    op.create_index('idx_expert_applications_email', 'expert_applications', ['email'])
    op.create_index('idx_expert_applications_status', 'expert_applications', ['status'])

    # ========================================================================
    # EXPERT QUALITY SCORES (calculated periodically)
    # ========================================================================
    op.create_table(
        'expert_quality_scores',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('expert_id', sa.String(36), sa.ForeignKey('experts.id', ondelete='CASCADE'), nullable=False),

        # Component scores (0-100)
        sa.Column('client_satisfaction_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('ai_agreement_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('response_time_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('task_completion_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('revision_rate_score', sa.Numeric(5, 2), nullable=True),

        # Overall score
        sa.Column('total_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('tier', sa.String(50), nullable=True),  # platinum, gold, silver, standard, probation

        # Timestamps
        sa.Column('calculated_at', sa.DateTime, default=sa.func.now()),
    )

    op.create_index('idx_quality_scores_expert_id', 'expert_quality_scores', ['expert_id'])
    op.create_index('idx_quality_scores_calculated_at', 'expert_quality_scores', ['calculated_at'])

    # ========================================================================
    # EXPERT REVIEWS (client feedback)
    # ========================================================================
    op.create_table(
        'expert_reviews',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('engagement_id', sa.String(36), sa.ForeignKey('expert_engagements.id'), nullable=False),
        sa.Column('customer_id', sa.String(36), sa.ForeignKey('customers.id'), nullable=False),
        sa.Column('expert_id', sa.String(36), sa.ForeignKey('experts.id'), nullable=False),

        # Ratings
        sa.Column('rating', sa.Integer, nullable=False),  # 1-5 stars
        sa.Column('review_text', sa.Text, nullable=True),
        sa.Column('nps_score', sa.Integer, nullable=True),  # 0-10

        # Specific ratings (optional)
        sa.Column('communication_rating', sa.Integer, nullable=True),
        sa.Column('quality_rating', sa.Integer, nullable=True),
        sa.Column('speed_rating', sa.Integer, nullable=True),
        sa.Column('value_rating', sa.Integer, nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
    )

    op.create_index('idx_expert_reviews_expert_id', 'expert_reviews', ['expert_id'])
    op.create_index('idx_expert_reviews_engagement_id', 'expert_reviews', ['engagement_id'])


def downgrade() -> None:
    op.drop_table('expert_reviews')
    op.drop_table('expert_quality_scores')
    op.drop_table('expert_applications')
    op.drop_table('expert_engagements')
    op.drop_table('expert_certifications')
    op.drop_table('expert_mcps')
    op.drop_table('experts')
