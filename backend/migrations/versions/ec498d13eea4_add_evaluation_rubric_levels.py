"""add_evaluation_rubric_levels

Revision ID: ec498d13eea4
Revises: 001
Create Date: 2025-11-09 01:21:45.804592

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'ec498d13eea4'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create evaluation_rubric_levels table
    op.create_table('evaluation_rubric_levels',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('criteria_id', sa.String(length=36), nullable=False),
    sa.Column('level_name', sa.String(length=50), nullable=False),
    sa.Column('level_order', sa.Integer(), nullable=False),
    sa.Column('min_score', sa.Integer(), nullable=False),
    sa.Column('max_score', sa.Integer(), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('examples', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['criteria_id'], ['evaluation_criteria.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    # Create index on criteria_id for better query performance
    op.create_index('ix_evaluation_rubric_levels_criteria_id', 'evaluation_rubric_levels', ['criteria_id'])


def downgrade() -> None:
    # Drop evaluation_rubric_levels table
    op.drop_index('ix_evaluation_rubric_levels_criteria_id', table_name='evaluation_rubric_levels')
    op.drop_table('evaluation_rubric_levels')

