"""add_customer_tone_to_evaluation

Revision ID: 50355ee2454a
Revises: ec498d13eea4
Create Date: 2025-11-09 01:49:37.321434

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '50355ee2454a'
down_revision = 'ec498d13eea4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add customer_tone column to evaluations table
    op.add_column('evaluations', sa.Column('customer_tone', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    # Remove customer_tone column from evaluations table
    op.drop_column('evaluations', 'customer_tone')
