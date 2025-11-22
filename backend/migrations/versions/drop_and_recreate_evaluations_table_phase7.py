"""drop_and_recreate_evaluations_table_phase7

Revision ID: drop_eval_phase7
Revises: 2d158adf48a9
Create Date: 2025-11-23 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'drop_eval_phase7'
down_revision = '2d158adf48a9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Drop and recreate evaluations table with clean Phase 7 schema.
    This will also drop dependent tables: category_scores, human_reviews, evaluation_versions, rule_engine_results
    """
    from sqlalchemy import inspect
    from sqlalchemy.exc import ProgrammingError, OperationalError
    
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Helper function to safely drop constraints
    def safe_drop_constraint(table_name, constraint_name):
        try:
            op.drop_constraint(constraint_name, table_name, type_='foreignkey')
        except (ProgrammingError, OperationalError):
            pass
    
    # Helper function to safely drop tables
    def safe_drop_table(table_name):
        # Check if table exists first
        if inspector.has_table(table_name):
            try:
                op.drop_table(table_name)
            except (ProgrammingError, OperationalError) as e:
                # If drop fails, try to rollback and continue
                conn.rollback()
                pass
    
    # Step 1: Drop dependent tables first (they have foreign keys to evaluations)
    safe_drop_table('category_scores')
    safe_drop_table('human_reviews')
    safe_drop_table('evaluation_versions')
    safe_drop_table('rule_engine_results')
    safe_drop_table('rule_engine_results_v2')
    
    # Step 2: Drop evaluations table
    safe_drop_table('evaluations')
    
    # Step 3: Recreate evaluations table with Phase 7 schema
    # Use existing enum types (they should already exist)
    evaluationstatus_enum = postgresql.ENUM('pending', 'completed', 'reviewed', name='evaluationstatus', create_type=False)
    reviewstatus_enum = postgresql.ENUM('pending', 'in_review', 'completed', 'disputed', name='reviewstatus', create_type=False)
    
    op.create_table(
        'evaluations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('recording_id', sa.String(36), sa.ForeignKey('recordings.id'), nullable=False, unique=True, index=True),
        sa.Column('evaluated_by_user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('overall_score', sa.Integer(), nullable=False),
        sa.Column('resolution_detected', sa.Boolean(), nullable=False),
        sa.Column('resolution_confidence', sa.Float(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('requires_human_review', sa.Boolean(), default=False, nullable=False),
        sa.Column('customer_tone', postgresql.JSONB(), nullable=True),
        sa.Column('llm_analysis', postgresql.JSONB(), nullable=False),
        sa.Column('status', evaluationstatus_enum, default='pending', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        
        # MVP Evaluation Improvements: Reproducibility metadata
        sa.Column('prompt_id', sa.String(100), nullable=True),
        sa.Column('prompt_version', sa.String(20), nullable=True),
        sa.Column('model_version', sa.String(50), nullable=True),
        sa.Column('model_temperature', sa.Float(), default=0.0, nullable=False),
        sa.Column('model_top_p', sa.Float(), default=1.0, nullable=False),
        sa.Column('llm_raw', postgresql.JSONB(), nullable=True),
        sa.Column('rubric_version', sa.String(20), nullable=True),
        sa.Column('evaluation_seed', sa.String(50), nullable=True),
        
        # Phase 1: Agent/Team associations
        sa.Column('agent_id', sa.String(36), sa.ForeignKey('users.id'), nullable=True, index=True),
        sa.Column('team_id', sa.String(36), sa.ForeignKey('teams.id'), nullable=True),
        
        # Phase 3-7: Standardized Phases - Store evaluation results
        sa.Column('deterministic_results', postgresql.JSONB(), nullable=True),
        sa.Column('llm_stage_evaluations', postgresql.JSONB(), nullable=True),
        sa.Column('final_evaluation', postgresql.JSONB(), nullable=True),
        sa.Column('flow_version_id', sa.String(36), sa.ForeignKey('flow_versions.id'), nullable=True),
        sa.Column('rubric_template_id', sa.String(36), sa.ForeignKey('rubric_templates.id'), nullable=True),
    )
    
    # Create index on created_at
    op.create_index('ix_evaluations_created_at', 'evaluations', ['created_at'])
    
    # Step 4: Recreate dependent tables
    # Category Scores
    op.create_table(
        'category_scores',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('evaluation_id', sa.String(36), sa.ForeignKey('evaluations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('category_name', sa.String(255), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('feedback', sa.Text(), nullable=True),
    )
    
    # Human Reviews
    op.create_table(
        'human_reviews',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('recording_id', sa.String(36), sa.ForeignKey('recordings.id'), nullable=False),
        sa.Column('evaluation_id', sa.String(36), sa.ForeignKey('evaluations.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('reviewer_user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('review_status', reviewstatus_enum, nullable=True, default='pending'),
        sa.Column('human_scores', postgresql.JSONB(), nullable=True),
        sa.Column('human_violations', postgresql.JSONB(), nullable=True),
        sa.Column('ai_scores', postgresql.JSONB(), nullable=True),
        sa.Column('delta', postgresql.JSONB(), nullable=True),
        sa.Column('reviewer_notes', sa.Text(), nullable=True),
        sa.Column('ai_score_accuracy', sa.Numeric(3, 1), nullable=True),
        sa.Column('human_overall_score', sa.Integer(), nullable=True),
        sa.Column('human_category_scores', postgresql.JSONB(), nullable=True),
        sa.Column('ai_recommendation', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, onupdate=sa.func.now()),
    )
    op.create_index('ix_human_reviews_created_at', 'human_reviews', ['created_at'])
    
    # Evaluation Versions
    op.create_table(
        'evaluation_versions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('evaluation_id', sa.String(36), sa.ForeignKey('evaluations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now(), index=True),
        sa.Column('created_by', sa.String(36), nullable=True),
        sa.Column('overall_score', sa.Integer(), nullable=False),
        sa.Column('confidence_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('category_scores', postgresql.JSONB(), nullable=False),
        sa.Column('violations', postgresql.JSONB(), nullable=True),
        sa.Column('llm_analysis', postgresql.JSONB(), nullable=True),
        sa.Column('model_used', sa.String(50), nullable=True),
        sa.Column('model_version', sa.String(50), nullable=True),
        sa.Column('processing_pipeline_version', sa.String(20), nullable=True),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('previous_version_id', sa.String(36), nullable=True),
        sa.Column('regulatory_compliance', postgresql.JSONB(), nullable=True),
        sa.Column('audit_trail_hash', sa.String(64), nullable=True),
    )
    
    # Rule Engine Results
    op.create_table(
        'rule_engine_results',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('recording_id', sa.String(36), sa.ForeignKey('recordings.id'), nullable=False),
        sa.Column('evaluation_id', sa.String(36), sa.ForeignKey('evaluations.id', ondelete='CASCADE'), nullable=True),
        sa.Column('rules', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now(), index=True),
    )
    
    # Rule Engine Results V2 (legacy, may not be used in Phase 7)
    try:
        op.create_table(
            'rule_engine_results_v2',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('evaluation_id', sa.String(36), sa.ForeignKey('evaluations.id', ondelete='CASCADE'), nullable=False, unique=True),
            sa.Column('policy_rules_version', sa.Integer(), nullable=True),
            sa.Column('rule_results', postgresql.JSONB(), nullable=False),
            sa.Column('execution_time_ms', sa.Integer(), nullable=True),
            sa.Column('transcript_segments_count', sa.Integer(), nullable=True),
            sa.Column('rules_evaluated_count', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        )
    except Exception:
        pass  # Table might not be needed


def downgrade() -> None:
    """
    Note: This migration drops data. Downgrade is not recommended.
    """
    op.drop_table('rule_engine_results')
    op.drop_table('evaluation_versions')
    op.drop_table('human_reviews')
    op.drop_table('category_scores')
    op.drop_table('evaluations')
    
    # Recreate old structure would require knowing the previous schema
    # This is intentionally left incomplete as downgrade is not recommended

