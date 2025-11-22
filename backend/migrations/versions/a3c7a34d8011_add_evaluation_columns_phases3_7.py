"""add_evaluation_columns_phases3_7

Revision ID: a3c7a34d8011
Revises: 35e8a2ba21c4
Create Date: 2025-11-22 23:16:38.417637

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'a3c7a34d8011'
down_revision = '35e8a2ba21c4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new JSONB columns to evaluations table
    op.add_column('evaluations', sa.Column('deterministic_results', postgresql.JSONB(), nullable=True))
    op.add_column('evaluations', sa.Column('llm_stage_evaluations', postgresql.JSONB(), nullable=True))
    op.add_column('evaluations', sa.Column('final_evaluation', postgresql.JSONB(), nullable=True))
    op.add_column('evaluations', sa.Column('flow_version_id', sa.String(36), nullable=True))
    op.add_column('evaluations', sa.Column('rubric_template_id', sa.String(36), nullable=True))
    
    # Add foreign keys
    op.create_foreign_key(
        'fk_evaluations_flow_version',
        'evaluations',
        'flow_versions',
        ['flow_version_id'],
        ['id']
    )
    op.create_foreign_key(
        'fk_evaluations_rubric_template',
        'evaluations',
        'rubric_templates',
        ['rubric_template_id'],
        ['id']
    )
    
    # Add indexes
    op.create_index('ix_evaluations_flow_version_id', 'evaluations', ['flow_version_id'])
    op.create_index('ix_evaluations_rubric_template_id', 'evaluations', ['rubric_template_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_evaluations_rubric_template_id', 'evaluations')
    op.drop_index('ix_evaluations_flow_version_id', 'evaluations')
    
    # Drop foreign keys
    op.drop_constraint('fk_evaluations_rubric_template', 'evaluations', type_='foreignkey')
    op.drop_constraint('fk_evaluations_flow_version', 'evaluations', type_='foreignkey')
    
    # Drop columns
    op.drop_column('evaluations', 'rubric_template_id')
    op.drop_column('evaluations', 'flow_version_id')
    op.drop_column('evaluations', 'final_evaluation')
    op.drop_column('evaluations', 'llm_stage_evaluations')
    op.drop_column('evaluations', 'deterministic_results')

