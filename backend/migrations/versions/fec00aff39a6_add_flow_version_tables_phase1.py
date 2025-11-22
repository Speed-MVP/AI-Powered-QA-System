"""add_flow_version_tables_phase1

Revision ID: fec00aff39a6
Revises: add_rule_editor_phase5
Create Date: 2025-11-22 23:13:43.208764

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'fec00aff39a6'
down_revision = 'add_rule_editor_phase5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create flow_versions table
    op.create_table(
        'flow_versions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('company_id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('version_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    
    # Create foreign key for flow_versions
    op.create_foreign_key(
        'fk_flow_versions_company',
        'flow_versions',
        'companies',
        ['company_id'],
        ['id']
    )
    
    # Create indexes for flow_versions
    op.create_index('ix_flow_versions_company_id', 'flow_versions', ['company_id'])
    op.create_index('ix_flow_versions_is_active', 'flow_versions', ['is_active'])
    
    # Create flow_stages table
    op.create_table(
        'flow_stages',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('flow_version_id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    
    # Create foreign key for flow_stages
    op.create_foreign_key(
        'fk_flow_stages_flow_version',
        'flow_stages',
        'flow_versions',
        ['flow_version_id'],
        ['id'],
        ondelete='CASCADE'
    )
    
    # Create indexes for flow_stages
    op.create_index('ix_flow_stages_flow_version_id', 'flow_stages', ['flow_version_id'])
    op.create_index('ix_flow_stages_order', 'flow_stages', ['flow_version_id', 'order'])
    
    # Create flow_steps table
    op.create_table(
        'flow_steps',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('stage_id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('required', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('expected_phrases', postgresql.JSONB(), nullable=True),
        sa.Column('timing_requirement', postgresql.JSONB(), nullable=True),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    
    # Create foreign key for flow_steps
    op.create_foreign_key(
        'fk_flow_steps_stage',
        'flow_steps',
        'flow_stages',
        ['stage_id'],
        ['id'],
        ondelete='CASCADE'
    )
    
    # Create indexes for flow_steps
    op.create_index('ix_flow_steps_stage_id', 'flow_steps', ['stage_id'])
    op.create_index('ix_flow_steps_order', 'flow_steps', ['stage_id', 'order'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_flow_steps_order', 'flow_steps')
    op.drop_index('ix_flow_steps_stage_id', 'flow_steps')
    op.drop_index('ix_flow_stages_order', 'flow_stages')
    op.drop_index('ix_flow_stages_flow_version_id', 'flow_stages')
    op.drop_index('ix_flow_versions_is_active', 'flow_versions')
    op.drop_index('ix_flow_versions_company_id', 'flow_versions')
    
    # Drop foreign keys
    op.drop_constraint('fk_flow_steps_stage', 'flow_steps', type_='foreignkey')
    op.drop_constraint('fk_flow_stages_flow_version', 'flow_stages', type_='foreignkey')
    op.drop_constraint('fk_flow_versions_company', 'flow_versions', type_='foreignkey')
    
    # Drop tables
    op.drop_table('flow_steps')
    op.drop_table('flow_stages')
    op.drop_table('flow_versions')

