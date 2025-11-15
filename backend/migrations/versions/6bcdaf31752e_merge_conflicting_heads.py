"""merge_conflicting_heads

Revision ID: 6bcdaf31752e
Revises: 0123456789ab, 397cf3d0efd2
Create Date: 2025-11-14 20:21:15.816841

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6bcdaf31752e'
down_revision = ('0123456789ab', '397cf3d0efd2')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

