"""add recording processing events table

Revision ID: b7f0d3c0831f
Revises: aa3d117db8d3
Create Date: 2025-11-17 18:55:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'b7f0d3c0831f'
down_revision = 'f2270565c41a'  # Fixed: references mvp_evaluation_improvements
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'recording_processing_events',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('recording_id', sa.String(length=36), nullable=False),
        sa.Column('stage', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('event_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['recording_id'], ['recordings.id'], ondelete='CASCADE')
    )
    op.create_index(
        'ix_recording_processing_events_recording_stage',
        'recording_processing_events',
        ['recording_id', 'stage'],
        unique=False
    )


def downgrade():
    op.drop_index('ix_recording_processing_events_recording_stage', table_name='recording_processing_events')
    op.drop_table('recording_processing_events')

