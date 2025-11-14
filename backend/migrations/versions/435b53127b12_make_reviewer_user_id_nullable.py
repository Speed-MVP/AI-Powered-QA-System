"""make_reviewer_user_id_nullable

Revision ID: 435b53127b12
Revises: 1015163832c8
Create Date: 2025-11-10 21:04:07.456045

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '435b53127b12'
down_revision = '1015163832c8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Make reviewer_user_id nullable in human_reviews table
    op.alter_column('human_reviews', 'reviewer_user_id',
                    existing_type=sa.String(36),
                    nullable=True)


def downgrade() -> None:
    # Make reviewer_user_id not nullable again
    op.alter_column('human_reviews', 'reviewer_user_id',
                    existing_type=sa.String(36),
                    nullable=False)

