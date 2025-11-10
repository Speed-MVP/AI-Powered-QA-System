"""make_human_review_fields_nullable

Revision ID: 397cf3d0efd2
Revises: 435b53127b12
Create Date: 2025-11-10 21:05:23.293957

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '397cf3d0efd2'
down_revision = '435b53127b12'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Make human review fields nullable since they're filled when review is submitted
    op.alter_column('human_reviews', 'human_overall_score',
                    existing_type=sa.Integer(),
                    nullable=True)
    op.alter_column('human_reviews', 'human_category_scores',
                    existing_type=sa.JSON(),
                    nullable=True)
    op.alter_column('human_reviews', 'ai_score_accuracy',
                    existing_type=sa.Numeric(3, 1),
                    nullable=True)


def downgrade() -> None:
    # Make human review fields not nullable again
    op.alter_column('human_reviews', 'human_overall_score',
                    existing_type=sa.Integer(),
                    nullable=False)
    op.alter_column('human_reviews', 'human_category_scores',
                    existing_type=sa.JSON(),
                    nullable=False)
    op.alter_column('human_reviews', 'ai_score_accuracy',
                    existing_type=sa.Numeric(3, 1),
                    nullable=False)

