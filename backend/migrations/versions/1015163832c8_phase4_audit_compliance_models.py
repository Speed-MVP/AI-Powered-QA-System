"""phase4_audit_compliance_models

Revision ID: 1015163832c8
Revises: e8dd70202a60
Create Date: 2025-11-10 04:14:35.227671

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1015163832c8'
down_revision = 'e8dd70202a60'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create audit event type enum if it doesn't exist
    audit_event_type = sa.Enum('evaluation_created', 'evaluation_updated', 'evaluation_reviewed', 'evaluation_overridden', 'model_changed', 'policy_updated', 'batch_processed', name='auditeventtype')
    audit_event_type.create(op.get_bind(), checkfirst=True)

    # Create audit_logs table
    op.create_table('audit_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('event_type', audit_event_type, nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('user_role', sa.String(length=50), nullable=True),
        sa.Column('old_values', sa.JSON(), nullable=True),
        sa.Column('new_values', sa.JSON(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('model_version', sa.String(length=50), nullable=True),
        sa.Column('confidence_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('compliance_flags', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_timestamp'), 'audit_logs', ['timestamp'], unique=False)

    # Create evaluation_versions table
    op.create_table('evaluation_versions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('evaluation_id', sa.String(length=36), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=True),
        sa.Column('overall_score', sa.Integer(), nullable=False),
        sa.Column('confidence_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('category_scores', sa.JSON(), nullable=False),
        sa.Column('violations', sa.JSON(), nullable=True),
        sa.Column('llm_analysis', sa.JSON(), nullable=True),
        sa.Column('model_used', sa.String(length=50), nullable=True),
        sa.Column('model_version', sa.String(length=50), nullable=True),
        sa.Column('processing_pipeline_version', sa.String(length=20), nullable=True),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('previous_version_id', sa.String(length=36), nullable=True),
        sa.Column('regulatory_compliance', sa.JSON(), nullable=True),
        sa.Column('audit_trail_hash', sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(['evaluation_id'], ['evaluations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_evaluation_versions_created_at'), 'evaluation_versions', ['created_at'], unique=False)
    op.create_index(op.f('ix_evaluation_versions_evaluation_id'), 'evaluation_versions', ['evaluation_id'], unique=False)

    # Create compliance_reports table
    op.create_table('compliance_reports',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('report_type', sa.String(length=50), nullable=False),
        sa.Column('report_period_start', sa.DateTime(), nullable=False),
        sa.Column('report_period_end', sa.DateTime(), nullable=False),
        sa.Column('generated_at', sa.DateTime(), nullable=True),
        sa.Column('total_evaluations', sa.Integer(), nullable=True),
        sa.Column('human_review_rate', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('average_confidence', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('model_accuracy_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('gdpr_compliant', sa.Boolean(), nullable=True),
        sa.Column('hipaa_compliant', sa.Boolean(), nullable=True),
        sa.Column('sox_compliant', sa.Boolean(), nullable=True),
        sa.Column('false_positive_rate', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('false_negative_rate', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('human_agreement_rate', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('evaluation_summary', sa.JSON(), nullable=True),
        sa.Column('violation_breakdown', sa.JSON(), nullable=True),
        sa.Column('model_performance', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('reviewed_by', sa.String(length=36), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('approved_by', sa.String(length=36), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create data_retention_policies table
    op.create_table('data_retention_policies',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('retention_period_days', sa.Integer(), nullable=False),
        sa.Column('retention_reason', sa.Text(), nullable=True),
        sa.Column('data_categories', sa.JSON(), nullable=True),
        sa.Column('legal_basis', sa.String(length=100), nullable=True),
        sa.Column('auto_delete', sa.Boolean(), nullable=True),
        sa.Column('deletion_method', sa.String(length=20), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    pass

