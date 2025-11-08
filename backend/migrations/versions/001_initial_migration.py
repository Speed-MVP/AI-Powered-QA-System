"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2025-11-08 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create companies table
    op.create_table(
        'companies',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('company_name', sa.String(255), nullable=False),
        sa.Column('industry', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('company_id', sa.String(36), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=True),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('role', sa.Enum('admin', 'qa_manager', 'reviewer', name='userrole'), nullable=False, server_default='reviewer'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_users_email', 'users', ['email'])
    
    # Create policy_templates table
    op.create_table(
        'policy_templates',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('company_id', sa.String(36), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('template_name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # Create evaluation_criteria table
    op.create_table(
        'evaluation_criteria',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('policy_template_id', sa.String(36), sa.ForeignKey('policy_templates.id'), nullable=False),
        sa.Column('category_name', sa.String(255), nullable=False),
        sa.Column('weight', sa.Numeric(5, 2), nullable=False),
        sa.Column('passing_score', sa.Integer(), nullable=False),
        sa.Column('evaluation_prompt', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # Create recordings table
    op.create_table(
        'recordings',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('company_id', sa.String(36), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('uploaded_by_user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_url', sa.Text(), nullable=False),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('queued', 'processing', 'completed', 'failed', name='recordingstatus'), nullable=False, server_default='queued'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_recordings_company_id', 'recordings', ['company_id'])
    op.create_index('ix_recordings_status', 'recordings', ['status'])
    op.create_index('ix_recordings_uploaded_at', 'recordings', ['uploaded_at'])
    
    # Create transcripts table
    op.create_table(
        'transcripts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('recording_id', sa.String(36), sa.ForeignKey('recordings.id'), nullable=False, unique=True),
        sa.Column('transcript_text', sa.Text(), nullable=False),
        sa.Column('diarized_segments', postgresql.JSONB, nullable=True),
        sa.Column('transcription_confidence', sa.Numeric(5, 2), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # Create evaluations table
    op.create_table(
        'evaluations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('recording_id', sa.String(36), sa.ForeignKey('recordings.id'), nullable=False, unique=True),
        sa.Column('policy_template_id', sa.String(36), sa.ForeignKey('policy_templates.id'), nullable=False),
        sa.Column('evaluated_by_user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('overall_score', sa.Integer(), nullable=False),
        sa.Column('resolution_detected', sa.Boolean(), nullable=False),
        sa.Column('resolution_confidence', sa.Float(), nullable=False),
        sa.Column('llm_analysis', postgresql.JSONB, nullable=False),
        sa.Column('status', sa.Enum('pending', 'completed', 'reviewed', name='evaluationstatus'), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_evaluations_recording_id', 'evaluations', ['recording_id'])
    op.create_index('ix_evaluations_created_at', 'evaluations', ['created_at'])
    
    # Create category_scores table
    op.create_table(
        'category_scores',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('evaluation_id', sa.String(36), sa.ForeignKey('evaluations.id'), nullable=False),
        sa.Column('category_name', sa.String(255), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('feedback', sa.Text(), nullable=True),
    )
    
    # Create policy_violations table
    op.create_table(
        'policy_violations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('evaluation_id', sa.String(36), sa.ForeignKey('evaluations.id'), nullable=False),
        sa.Column('criteria_id', sa.String(36), sa.ForeignKey('evaluation_criteria.id'), nullable=False),
        sa.Column('violation_type', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('severity', sa.Enum('critical', 'major', 'minor', name='violationseverity'), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('policy_violations')
    op.drop_table('category_scores')
    op.drop_table('evaluations')
    op.drop_table('transcripts')
    op.drop_table('recordings')
    op.drop_table('evaluation_criteria')
    op.drop_table('policy_templates')
    op.drop_table('users')
    op.drop_table('companies')
    
    # Drop enums
    sa.Enum(name='violationseverity').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='evaluationstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='recordingstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='userrole').drop(op.get_bind(), checkfirst=True)

