"""remove_all_legacy_tables

Revision ID: remove_legacy_tables_2025
Revises: add_blueprint_phase2
Create Date: 2025-11-24 15:00:00.000000

This migration removes all legacy FlowVersion/FlowStage/FlowStep system tables
and legacy compliance_rules and rubric_templates tables.
The system now exclusively uses the Blueprint-based architecture.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.exc import ProgrammingError, OperationalError


# revision identifiers, used by Alembic.
revision = 'remove_legacy_tables_2025'
down_revision = 'add_blueprint_phase2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Remove all legacy FlowVersion/FlowStage/FlowStep system tables and
    legacy compliance_rules and rubric_templates tables.
    """
    conn = op.get_bind()
    inspector = inspect(conn)
    
    def safe_drop_constraint(table_name, constraint_name):
        """Safely drop a constraint if it exists"""
        try:
            if inspector.has_table(table_name):
                constraints = [c['name'] for c in inspector.get_foreign_keys(table_name)]
                if constraint_name in constraints:
                    op.drop_constraint(constraint_name, table_name, type_='foreignkey')
        except (ProgrammingError, OperationalError, AttributeError, KeyError):
            pass
    
    def safe_drop_index(table_name, index_name):
        """Safely drop an index if it exists"""
        try:
            if inspector.has_table(table_name):
                indexes = [idx['name'] for idx in inspector.get_indexes(table_name)]
                if index_name in indexes:
                    op.drop_index(index_name, table_name)
        except (ProgrammingError, OperationalError, AttributeError, KeyError):
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
        except (ProgrammingError, OperationalError, AttributeError, KeyError):
            pass
    
    # Step 1: Drop foreign key constraints for legacy tables
    # Drop constraints on flow_steps
    for constraint_name in ['fk_flow_steps_stage', 'flow_steps_stage_id_fkey']:
        safe_drop_constraint('flow_steps', constraint_name)
    
    # Drop constraints on flow_stages
    for constraint_name in ['fk_flow_stages_flow_version', 'flow_stages_flow_version_id_fkey']:
        safe_drop_constraint('flow_stages', constraint_name)
    
    # Drop constraints on flow_versions
    for constraint_name in ['fk_flow_versions_company', 'flow_versions_company_id_fkey']:
        safe_drop_constraint('flow_versions', constraint_name)
    
    # Drop constraints on compliance_rules (legacy)
    for constraint_name in ['fk_compliance_rules_flow_version', 'compliance_rules_flow_version_id_fkey']:
        safe_drop_constraint('compliance_rules', constraint_name)
    
    # Drop constraints on rubric_templates (legacy)
    for constraint_name in ['fk_rubric_templates_flow_version', 'rubric_templates_flow_version_id_fkey',
                          'fk_rubric_templates_created_by', 'rubric_templates_created_by_user_id_fkey']:
        safe_drop_constraint('rubric_templates', constraint_name)
    
    # Drop constraints on rubric_categories
    for constraint_name in ['fk_rubric_categories_template', 'rubric_categories_rubric_template_id_fkey']:
        safe_drop_constraint('rubric_categories', constraint_name)
    
    # Drop constraints on rubric_mappings
    for constraint_name in ['fk_rubric_mappings_category', 'rubric_mappings_rubric_category_id_fkey']:
        safe_drop_constraint('rubric_mappings', constraint_name)
    
    # Step 2: Drop indexes for legacy tables
    safe_drop_index('flow_steps', 'ix_flow_steps_order')
    safe_drop_index('flow_steps', 'ix_flow_steps_stage_id')
    safe_drop_index('flow_stages', 'ix_flow_stages_order')
    safe_drop_index('flow_stages', 'ix_flow_stages_flow_version_id')
    safe_drop_index('flow_versions', 'ix_flow_versions_is_active')
    safe_drop_index('flow_versions', 'ix_flow_versions_company_id')
    safe_drop_index('compliance_rules', 'ix_compliance_rules_active')
    safe_drop_index('compliance_rules', 'ix_compliance_rules_flow_version_id')
    safe_drop_index('rubric_templates', 'ix_rubric_templates_is_active')
    safe_drop_index('rubric_templates', 'ix_rubric_templates_flow_version_id')
    safe_drop_index('rubric_categories', 'ix_rubric_categories_template_id')
    safe_drop_index('rubric_mappings', 'ix_rubric_mappings_category_id')
    
    # Step 3: Drop legacy tables in dependency order
    # Drop child tables first
    safe_drop_table('rubric_mappings')
    safe_drop_table('rubric_categories')
    safe_drop_table('rubric_templates')  # Legacy Phase 5
    safe_drop_table('compliance_rules')  # Legacy Phase 2
    safe_drop_table('flow_steps')  # Legacy Phase 1
    safe_drop_table('flow_stages')  # Legacy Phase 1
    safe_drop_table('flow_versions')  # Legacy Phase 1
    
    # Step 4: Drop ENUM types if they're not used elsewhere
    # Note: We only drop if they're not used by compiled_* tables
    # ruletype and severity might still be used, so we check first
    try:
        # Check if ruletype is used elsewhere
        result = conn.execute(sa.text("""
            SELECT COUNT(*) FROM information_schema.columns 
            WHERE udt_name = 'ruletype'
        """))
        if result.scalar() == 0:
            op.execute("DROP TYPE IF EXISTS ruletype CASCADE")
    except:
        pass
    
    try:
        # Check if severity is used elsewhere (it's used in compiled_compliance_rules)
        # So we don't drop it
        pass
    except:
        pass


def downgrade() -> None:
    """
    Note: This migration removes legacy tables permanently.
    Downgrade is not recommended as it would require recreating all legacy data.
    Legacy system has been completely replaced by Blueprint system.
    """
    # Downgrade not implemented - legacy system removed permanently
    pass



