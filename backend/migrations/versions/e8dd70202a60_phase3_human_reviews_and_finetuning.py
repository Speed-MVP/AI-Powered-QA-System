"""phase3_human_reviews_and_finetuning

Revision ID: e8dd70202a60
Revises: 7a12d5c149c0
Create Date: 2025-11-10 03:58:48.747755

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e8dd70202a60'
down_revision = '7a12d5c149c0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create human_reviews table
    op.create_table('human_reviews',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('evaluation_id', sa.String(length=36), nullable=False),
        sa.Column('reviewer_user_id', sa.String(length=36), nullable=False),
        sa.Column('human_overall_score', sa.Integer(), nullable=False),
        sa.Column('human_category_scores', sa.JSON(), nullable=False),
        sa.Column('ai_score_accuracy', sa.Numeric(precision=3, scale=1), nullable=False),
        sa.Column('ai_recommendation', sa.Text(), nullable=True),
        sa.Column('review_status', sa.Enum('pending', 'in_review', 'completed', 'disputed', name='reviewstatus'), nullable=True),
        sa.Column('time_spent_seconds', sa.Integer(), nullable=True),
        sa.Column('difficulty_rating', sa.Numeric(precision=2, scale=1), nullable=True),
        sa.Column('included_in_training', sa.Boolean(), nullable=True),
        sa.Column('training_split', sa.String(length=20), nullable=True),
        sa.Column('training_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['evaluation_id'], ['evaluations.id'], ),
        sa.ForeignKeyConstraint(['reviewer_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('evaluation_id')
    )
    op.create_index(op.f('ix_human_reviews_created_at'), 'human_reviews', ['created_at'], unique=False)

    # Create fine_tuning_datasets table
    op.create_table('fine_tuning_datasets',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('total_samples', sa.Integer(), nullable=True),
        sa.Column('training_samples', sa.Integer(), nullable=True),
        sa.Column('validation_samples', sa.Integer(), nullable=True),
        sa.Column('test_samples', sa.Integer(), nullable=True),
        sa.Column('model_version', sa.String(length=50), nullable=False),
        sa.Column('fine_tuning_job_id', sa.String(length=255), nullable=True),
        sa.Column('fine_tuning_status', sa.String(length=50), nullable=True),
        sa.Column('baseline_accuracy', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('fine_tuned_accuracy', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('human_agreement_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('version', sa.String(length=20), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_fine_tuning_datasets_created_at'), 'fine_tuning_datasets', ['created_at'], unique=False)

    # Create fine_tuning_samples table
    op.create_table('fine_tuning_samples',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('dataset_id', sa.String(length=36), nullable=False),
        sa.Column('transcript_text', sa.Text(), nullable=False),
        sa.Column('diarized_segments', sa.JSON(), nullable=True),
        sa.Column('sentiment_analysis', sa.JSON(), nullable=True),
        sa.Column('voice_baselines', sa.JSON(), nullable=True),
        sa.Column('call_metadata', sa.JSON(), nullable=True),
        sa.Column('policy_template_id', sa.String(length=36), nullable=True),
        sa.Column('expected_category_scores', sa.JSON(), nullable=False),
        sa.Column('expected_violations', sa.JSON(), nullable=True),
        sa.Column('expected_overall_score', sa.Integer(), nullable=False),
        sa.Column('source_evaluation_id', sa.String(length=36), nullable=True),
        sa.Column('quality_score', sa.Numeric(precision=3, scale=1), nullable=True),
        sa.Column('difficulty_level', sa.String(length=20), nullable=True),
        sa.Column('split', sa.String(length=20), nullable=False),
        sa.Column('used_in_training', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['dataset_id'], ['fine_tuning_datasets.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create model_performance table
    op.create_table('model_performance',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('model_version', sa.String(length=50), nullable=False),
        sa.Column('fine_tuning_dataset_id', sa.String(length=36), nullable=True),
        sa.Column('accuracy_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('precision_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('recall_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('f1_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('human_agreement_rate', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('false_positive_rate', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('false_negative_rate', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('total_evaluations', sa.Integer(), nullable=False),
        sa.Column('evaluation_period_start', sa.DateTime(), nullable=False),
        sa.Column('evaluation_period_end', sa.DateTime(), nullable=False),
        sa.Column('avg_confidence_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('confidence_threshold', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('human_review_rate', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['fine_tuning_dataset_id'], ['fine_tuning_datasets.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_model_performance_created_at'), 'model_performance', ['created_at'], unique=False)


def downgrade() -> None:
    pass

