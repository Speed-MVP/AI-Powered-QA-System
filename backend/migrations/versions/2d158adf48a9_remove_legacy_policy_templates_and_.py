"""remove_legacy_policy_templates_and_criteria

Revision ID: 2d158adf48a9
Revises: cfa9ea41e5b2
Create Date: 2025-11-23 04:33:39.892960

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '2d158adf48a9'
down_revision = 'cfa9ea41e5b2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Remove all legacy Policy Template system tables and foreign keys.
    The new system uses FlowVersion + RubricTemplate + ComplianceRule.
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
    
    # Step 1: Drop foreign key constraints that reference policy_templates
    # Try multiple possible constraint names
    for constraint_name in ['fk_rubric_templates_policy_template', 'rubric_templates_policy_template_id_fkey']:
        safe_drop_constraint('rubric_templates', constraint_name)
    
    for constraint_name in ['evaluations_policy_template_id_fkey', 'fk_evaluations_policy_template']:
        safe_drop_constraint('evaluations', constraint_name)
    
    safe_drop_constraint('policy_templates', 'fk_policy_templates_rules_approved_by_user')
    
    # Step 2: Drop tables that reference policy_templates (in dependency order)
    safe_drop_table('policy_violations')
    safe_drop_table('evaluation_rubric_levels')
    safe_drop_table('evaluation_criteria')
    safe_drop_table('policy_rules_versions')
    safe_drop_table('policy_rules_drafts')
    safe_drop_table('rule_audit_logs')
    safe_drop_table('rule_drafts')
    safe_drop_table('rule_versions')
    safe_drop_table('policy_clarifications')
    safe_drop_table('policy_templates')
    
    # Step 3: Remove policy_template_id columns from remaining tables
    safe_drop_column('rubric_templates', 'policy_template_id')
    safe_drop_column('evaluations', 'policy_template_id')
    safe_drop_column('human_reviews', 'policy_template_id')


def downgrade() -> None:
    """
    Note: This migration removes legacy tables permanently.
    Downgrade is not recommended as it would require recreating all legacy data.
    """
    # Downgrade not implemented - legacy system removed permanently
    pass
