"""mvp_evaluation_improvements

Revision ID: f2270565c41a
Revises: 6bcdaf31752e
Create Date: 2025-11-14 20:21:18.238674

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f2270565c41a'
down_revision = '6bcdaf31752e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add reproducibility metadata to evaluations table
    op.add_column('evaluations', sa.Column('prompt_id', sa.String(length=100), nullable=True))
    op.add_column('evaluations', sa.Column('prompt_version', sa.String(length=20), nullable=True))
    op.add_column('evaluations', sa.Column('model_version', sa.String(length=50), nullable=True))
    op.add_column('evaluations', sa.Column('model_temperature', sa.Float(), nullable=True, default=0.0))
    op.add_column('evaluations', sa.Column('model_top_p', sa.Float(), nullable=True, default=1.0))
    op.add_column('evaluations', sa.Column('llm_raw', sa.JSON(), nullable=True))
    op.add_column('evaluations', sa.Column('rubric_version', sa.String(length=20), nullable=True))
    op.add_column('evaluations', sa.Column('evaluation_seed', sa.String(length=50), nullable=True))

    # 2. Add quality metrics to transcripts table
    op.add_column('transcripts', sa.Column('deepgram_confidence', sa.Float(), nullable=True))
    op.add_column('transcripts', sa.Column('normalized_text', sa.Text(), nullable=True))

    # 3. Modify human_reviews table to match spec structure
    # Remove old columns that don't match spec
    op.drop_column('human_reviews', 'human_overall_score')
    op.drop_column('human_reviews', 'ai_score_accuracy')
    op.drop_column('human_reviews', 'review_status')
    op.drop_column('human_reviews', 'time_spent_seconds')
    op.drop_column('human_reviews', 'difficulty_rating')
    op.drop_column('human_reviews', 'included_in_training')
    op.drop_column('human_reviews', 'training_split')
    op.drop_column('human_reviews', 'training_notes')

    # Add spec-compliant columns
    op.add_column('human_reviews', sa.Column('human_scores', sa.JSON(), nullable=True))  # category -> score
    op.add_column('human_reviews', sa.Column('human_violations', sa.JSON(), nullable=True))  # list of violations with evidence
    op.add_column('human_reviews', sa.Column('ai_scores', sa.JSON(), nullable=True))  # snapshot of AI scores for comparison
    op.add_column('human_reviews', sa.Column('delta', sa.JSON(), nullable=True))  # computed ai->human differences
    op.add_column('human_reviews', sa.Column('reviewer_notes', sa.Text(), nullable=True))

    # Make reviewer_user_id nullable as per spec (allows anonymous reviews)
    op.alter_column('human_reviews', 'reviewer_user_id', nullable=True)

    # 4. Create rule_engine_results table
    op.create_table('rule_engine_results',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('recording_id', sa.String(length=36), nullable=False),
        sa.Column('evaluation_id', sa.String(length=36), nullable=True),
        sa.Column('rules', sa.JSON(), nullable=False),  # map(rule_name -> {hit: bool, evidence, severity})
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['recording_id'], ['recordings.id'], ),
        sa.ForeignKeyConstraint(['evaluation_id'], ['evaluations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # 5. Note: Indexes are handled separately to avoid conflicts with existing schema


def downgrade() -> None:
    # Remove indexes (conditional to avoid errors if they don't exist)
    try:
        op.drop_index(op.f('ix_rule_engine_results_created_at'), table_name='rule_engine_results')
    except:
        pass  # Index may not exist

    try:
        op.drop_index(op.f('ix_human_reviews_created_at'), table_name='human_reviews')
    except:
        pass  # Index may not exist

    try:
        op.drop_index(op.f('ix_evaluations_requires_human_review'), table_name='evaluations')
    except:
        pass  # Index may not exist

    try:
        op.drop_index(op.f('ix_recordings_status'), table_name='recordings')
    except:
        pass  # Index may not exist

    # Drop rule_engine_results table
    op.drop_table('rule_engine_results')

    # Revert human_reviews table changes
    op.alter_column('human_reviews', 'reviewer_user_id', nullable=False)
    op.drop_column('human_reviews', 'reviewer_notes')
    op.drop_column('human_reviews', 'delta')
    op.drop_column('human_reviews', 'ai_scores')
    op.drop_column('human_reviews', 'human_violations')
    op.drop_column('human_reviews', 'human_scores')

    # Add back old columns (this is approximate since we can't know exact original state)
    op.add_column('human_reviews', sa.Column('training_notes', sa.Text(), nullable=True))
    op.add_column('human_reviews', sa.Column('training_split', sa.String(length=20), nullable=True))
    op.add_column('human_reviews', sa.Column('included_in_training', sa.Boolean(), nullable=True))
    op.add_column('human_reviews', sa.Column('difficulty_rating', sa.Numeric(precision=2, scale=1), nullable=True))
    op.add_column('human_reviews', sa.Column('time_spent_seconds', sa.Integer(), nullable=True))
    op.add_column('human_reviews', sa.Column('review_status', sa.Enum('pending', 'in_review', 'completed', 'disputed', name='reviewstatus'), nullable=True))
    op.add_column('human_reviews', sa.Column('ai_recommendation', sa.Text(), nullable=True))
    op.add_column('human_reviews', sa.Column('ai_score_accuracy', sa.Numeric(precision=3, scale=1), nullable=True))
    op.add_column('human_reviews', sa.Column('human_overall_score', sa.Integer(), nullable=True))

    # Remove transcript columns
    op.drop_column('transcripts', 'normalized_text')
    op.drop_column('transcripts', 'deepgram_confidence')

    # Remove evaluation columns
    op.drop_column('evaluations', 'evaluation_seed')
    op.drop_column('evaluations', 'rubric_version')
    op.drop_column('evaluations', 'llm_raw')
    op.drop_column('evaluations', 'model_top_p')
    op.drop_column('evaluations', 'model_temperature')
    op.drop_column('evaluations', 'model_version')
    op.drop_column('evaluations', 'prompt_version')
    op.drop_column('evaluations', 'prompt_id')

