"""add_confidence_fields_to_evaluation

Revision ID: 7a12d5c149c0
Revises: cca6c2c11b1a
Create Date: 2025-11-10 03:52:41.577329

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7a12d5c149c0'
down_revision = 'cca6c2c11b1a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add confidence_score column
    op.add_column('evaluations', sa.Column('confidence_score', sa.Float(), nullable=True))
    # Add requires_human_review column
    op.add_column('evaluations', sa.Column('requires_human_review', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    # Remove confidence_score column
    op.drop_column('evaluations', 'confidence_score')
    # Remove requires_human_review column
    op.drop_column('evaluations', 'requires_human_review')

