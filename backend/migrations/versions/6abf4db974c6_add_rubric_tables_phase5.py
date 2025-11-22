"""add_rubric_tables_phase5

Revision ID: 6abf4db974c6
Revises: a3c7a34d8011
Create Date: 2025-11-22 23:16:51.066385

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '6abf4db974c6'
down_revision = 'a3c7a34d8011'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create rubric_templates table
    op.create_table(
        'rubric_templates',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('policy_template_id', sa.String(36), nullable=True),
        sa.Column('flow_version_id', sa.String(36), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_by_user_id', sa.String(36), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    
    # Create rubric_categories table
    op.create_table(
        'rubric_categories',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('rubric_template_id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('weight', sa.Numeric(5, 2), nullable=False),
        sa.Column('pass_threshold', sa.Integer(), nullable=False, server_default='75'),
        sa.Column('level_definitions', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    
    # Create rubric_mappings table
    op.create_table(
        'rubric_mappings',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('rubric_category_id', sa.String(36), nullable=False),
        sa.Column('target_type', sa.String(20), nullable=False),
        sa.Column('target_id', sa.String(36), nullable=False),
        sa.Column('contribution_weight', sa.Numeric(5, 2), nullable=False, server_default='1.0'),
        sa.Column('required_flag', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    
    # Create foreign keys
    op.create_foreign_key(
        'fk_rubric_templates_policy_template',
        'rubric_templates',
        'policy_templates',
        ['policy_template_id'],
        ['id']
    )
    op.create_foreign_key(
        'fk_rubric_templates_flow_version',
        'rubric_templates',
        'flow_versions',
        ['flow_version_id'],
        ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'fk_rubric_templates_created_by',
        'rubric_templates',
        'users',
        ['created_by_user_id'],
        ['id']
    )
    op.create_foreign_key(
        'fk_rubric_categories_template',
        'rubric_categories',
        'rubric_templates',
        ['rubric_template_id'],
        ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'fk_rubric_mappings_category',
        'rubric_mappings',
        'rubric_categories',
        ['rubric_category_id'],
        ['id'],
        ondelete='CASCADE'
    )
    
    # Create indexes
    op.create_index('ix_rubric_templates_flow_version_id', 'rubric_templates', ['flow_version_id'])
    op.create_index('ix_rubric_templates_is_active', 'rubric_templates', ['is_active'])
    op.create_index('ix_rubric_categories_template_id', 'rubric_categories', ['rubric_template_id'])
    op.create_index('ix_rubric_mappings_category_id', 'rubric_mappings', ['rubric_category_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_rubric_mappings_category_id', 'rubric_mappings')
    op.drop_index('ix_rubric_categories_template_id', 'rubric_categories')
    op.drop_index('ix_rubric_templates_is_active', 'rubric_templates')
    op.drop_index('ix_rubric_templates_flow_version_id', 'rubric_templates')
    
    # Drop foreign keys
    op.drop_constraint('fk_rubric_mappings_category', 'rubric_mappings', type_='foreignkey')
    op.drop_constraint('fk_rubric_categories_template', 'rubric_categories', type_='foreignkey')
    op.drop_constraint('fk_rubric_templates_created_by', 'rubric_templates', type_='foreignkey')
    op.drop_constraint('fk_rubric_templates_flow_version', 'rubric_templates', type_='foreignkey')
    op.drop_constraint('fk_rubric_templates_policy_template', 'rubric_templates', type_='foreignkey')
    
    # Drop tables
    op.drop_table('rubric_mappings')
    op.drop_table('rubric_categories')
    op.drop_table('rubric_templates')

