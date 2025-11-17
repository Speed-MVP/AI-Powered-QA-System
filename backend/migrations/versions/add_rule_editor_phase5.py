"""Add rule editor models (Phase 5)

Revision ID: add_rule_editor_phase5
Revises: add_policy_rules_phase1
Create Date: 2025-01-27 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_rule_editor_phase5'
down_revision = 'add_policy_rules_phase1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check existing tables to make migration idempotent
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()
    
    # Create policy_clarifications table (Phase 2)
    if 'policy_clarifications' not in existing_tables:
        op.create_table(
            'policy_clarifications',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('policy_template_id', sa.String(36), sa.ForeignKey('policy_templates.id'), nullable=False),
            sa.Column('question_id', sa.String(100), nullable=False),
            sa.Column('question', sa.Text(), nullable=False),
            sa.Column('answer', sa.Text(), nullable=True),
            sa.Column('answered_by_user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('answered_at', sa.DateTime(), nullable=True),
            sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        )
    
    # Create rule_drafts table (Phase 5)
    if 'rule_drafts' not in existing_tables:
        op.create_table(
            'rule_drafts',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('policy_template_id', sa.String(36), sa.ForeignKey('policy_templates.id'), nullable=False),
            sa.Column('rules_json', postgresql.JSONB(), nullable=False),
            sa.Column('status', sa.Enum('editing', 'needs_clarification', 'ready_for_confirm', 'validation_failed', 'failed', name='draftstatus'), nullable=False, server_default='editing'),
            sa.Column('created_by_user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        )
    
    # Create rule_versions table (Phase 5)
    if 'rule_versions' not in existing_tables:
        op.create_table(
            'rule_versions',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('policy_template_id', sa.String(36), sa.ForeignKey('policy_templates.id'), nullable=False),
            sa.Column('rules_json', postgresql.JSONB(), nullable=False),
            sa.Column('rules_hash', sa.String(64), nullable=False),
            sa.Column('rules_version', sa.Integer(), nullable=False),
            sa.Column('created_by_user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('llm_generated_flag', sa.Boolean(), nullable=False, server_default='false'),
        )
    
    # Create rule_audit_logs table (Phase 5)
    if 'rule_audit_logs' not in existing_tables:
        op.create_table(
            'rule_audit_logs',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('policy_template_id', sa.String(36), sa.ForeignKey('policy_templates.id'), nullable=False),
            sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('ip_address', sa.String(45), nullable=True),
            sa.Column('action', sa.String(50), nullable=False),
            sa.Column('delta', postgresql.JSONB(), nullable=True),
            sa.Column('reason', sa.Text(), nullable=True),
            sa.Column('rules_hash', sa.String(64), nullable=True),
            sa.Column('draft_id', sa.String(36), nullable=True),
            sa.Column('version_id', sa.String(36), nullable=True),
            sa.Column('llm_generated', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        )
    
    # Create indexes (check if they exist first)
    existing_indexes = [idx['name'] for idx in inspector.get_indexes('rule_drafts')] if 'rule_drafts' in existing_tables else []
    if 'ix_rule_drafts_policy_template' not in existing_indexes:
        try:
            op.create_index('ix_rule_drafts_policy_template', 'rule_drafts', ['policy_template_id'])
        except:
            pass
    
    existing_indexes = [idx['name'] for idx in inspector.get_indexes('rule_versions')] if 'rule_versions' in existing_tables else []
    if 'ix_rule_versions_policy_template' not in existing_indexes:
        try:
            op.create_index('ix_rule_versions_policy_template', 'rule_versions', ['policy_template_id'])
        except:
            pass
    
    existing_indexes = [idx['name'] for idx in inspector.get_indexes('rule_audit_logs')] if 'rule_audit_logs' in existing_tables else []
    if 'ix_rule_audit_logs_policy_template' not in existing_indexes:
        try:
            op.create_index('ix_rule_audit_logs_policy_template', 'rule_audit_logs', ['policy_template_id'])
        except:
            pass
    if 'ix_rule_audit_logs_user' not in existing_indexes:
        try:
            op.create_index('ix_rule_audit_logs_user', 'rule_audit_logs', ['user_id'])
        except:
            pass


def downgrade() -> None:
    op.drop_index('ix_rule_audit_logs_user', 'rule_audit_logs')
    op.drop_index('ix_rule_audit_logs_policy_template', 'rule_audit_logs')
    op.drop_index('ix_rule_versions_policy_template', 'rule_versions')
    op.drop_index('ix_rule_drafts_policy_template', 'rule_drafts')
    
    op.drop_table('rule_audit_logs')
    op.drop_table('rule_versions')
    op.drop_table('rule_drafts')
    op.drop_table('policy_clarifications')
    
    sa.Enum(name='draftstatus').drop(op.get_bind(), checkfirst=True)

