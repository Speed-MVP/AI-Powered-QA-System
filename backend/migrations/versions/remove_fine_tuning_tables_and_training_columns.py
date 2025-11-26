"""remove_fine_tuning_tables_and_training_columns

Revision ID: remove_finetuning_2025
Revises: a3c7a34d8011
Create Date: 2025-11-23 05:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'remove_finetuning_2025'
down_revision = 'a3c7a34d8011'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Remove all fine-tuning related tables and training columns from human_reviews.
    Fine-tuning is no longer used - Human Review is for overrides/audit only.
    """
    from sqlalchemy import inspect
    from sqlalchemy.exc import ProgrammingError, OperationalError
    
    conn = op.get_bind()
    inspector = inspect(conn)
    
    def safe_drop_constraint(table_name, constraint_name):
        """Safely drop a constraint if it exists"""
        try:
            constraints = [c['name'] for c in inspector.get_foreign_keys(table_name)]
            if constraint_name in constraints:
                op.drop_constraint(constraint_name, table_name, type_='foreignkey')
        except (ProgrammingError, OperationalError, AttributeError):
            pass
    
    def safe_drop_table(table_name):
        """Safely drop a table if it exists"""
        try:
            if inspector.has_table(table_name):
                op.drop_table(table_name)
        except (ProgrammingError, OperationalError, AttributeError):
            pass
    
    def safe_drop_column(table_name, column_name):
        """Safely drop a column if it exists"""
        try:
            if inspector.has_table(table_name):
                columns = [c['name'] for c in inspector.get_columns(table_name)]
                if column_name in columns:
                    op.drop_column(table_name, column_name)
        except (ProgrammingError, OperationalError, AttributeError):
            pass
    
    # Step 1: Drop foreign key constraints
    safe_drop_constraint('model_performance', 'model_performance_fine_tuning_dataset_id_fkey')
    safe_drop_constraint('fine_tuning_samples', 'fine_tuning_samples_dataset_id_fkey')
    
    # Step 2: Drop fine-tuning tables (in dependency order)
    safe_drop_table('model_performance')
    safe_drop_table('fine_tuning_samples')
    safe_drop_table('fine_tuning_datasets')
    
    # Step 3: Remove training-related columns from human_reviews
    safe_drop_column('human_reviews', 'included_in_training')
    safe_drop_column('human_reviews', 'training_split')
    safe_drop_column('human_reviews', 'training_notes')


def downgrade() -> None:
    """
    Note: This migration removes fine-tuning tables permanently.
    Downgrade is not recommended as fine-tuning is no longer part of the architecture.
    """
    # Downgrade not implemented - fine-tuning system removed permanently
    pass


