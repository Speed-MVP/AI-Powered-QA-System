"""Add policy_rules fields to policy_templates

Revision ID: add_policy_rules_phase1
Revises: b7f0d3c0831f
Create Date: 2025-01-27 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_policy_rules_phase1'
down_revision = 'b7f0d3c0831f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add Phase 1: Structured Rules Foundation columns to policy_templates
    op.add_column('policy_templates', sa.Column('policy_rules', postgresql.JSONB(), nullable=True))
    op.add_column('policy_templates', sa.Column('policy_rules_version', sa.Integer(), nullable=True))
    op.add_column('policy_templates', sa.Column('rules_generated_at', sa.DateTime(), nullable=True))
    op.add_column('policy_templates', sa.Column('rules_approved_by_user_id', sa.String(36), nullable=True))
    op.add_column('policy_templates', sa.Column('rules_generation_method', sa.String(20), nullable=True))
    op.add_column('policy_templates', sa.Column('enable_structured_rules', sa.Boolean(), nullable=False, server_default='false'))
    
    # Add foreign key constraint for rules_approved_by_user_id
    op.create_foreign_key(
        'fk_policy_templates_rules_approved_by_user',
        'policy_templates',
        'users',
        ['rules_approved_by_user_id'],
        ['id']
    )


def downgrade() -> None:
    # Drop foreign key constraint
    op.drop_constraint('fk_policy_templates_rules_approved_by_user', 'policy_templates', type_='foreignkey')
    
    # Drop columns
    op.drop_column('policy_templates', 'enable_structured_rules')
    op.drop_column('policy_templates', 'rules_generation_method')
    op.drop_column('policy_templates', 'rules_approved_by_user_id')
    op.drop_column('policy_templates', 'rules_generated_at')
    op.drop_column('policy_templates', 'policy_rules_version')
    op.drop_column('policy_templates', 'policy_rules')

