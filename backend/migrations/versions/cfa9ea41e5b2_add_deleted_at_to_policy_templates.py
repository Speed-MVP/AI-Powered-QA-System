"""add_deleted_at_to_policy_templates

Revision ID: cfa9ea41e5b2
Revises: 6abf4db974c6
Create Date: 2025-11-23 04:13:05.098395

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cfa9ea41e5b2'
down_revision = '6abf4db974c6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add deleted_at column for soft deletion
    op.add_column('policy_templates', sa.Column('deleted_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    # Remove deleted_at column
    op.drop_column('policy_templates', 'deleted_at')

