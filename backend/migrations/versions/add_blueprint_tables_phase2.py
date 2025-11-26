"""add_blueprint_tables_phase2

Revision ID: add_blueprint_phase2
Revises: remove_legacy_blueprint
Create Date: 2025-11-24 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_blueprint_phase2'
down_revision = 'remove_legacy_blueprint'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ENUM types
    blueprintstatus_enum = postgresql.ENUM('draft', 'published', 'archived', name='blueprintstatus', create_type=True)
    behavior_type_enum = postgresql.ENUM('required', 'optional', 'forbidden', 'critical', name='behaviortype', create_type=True)
    detection_mode_enum = postgresql.ENUM('semantic', 'exact_phrase', 'hybrid', name='detectionmode', create_type=True)
    critical_action_enum = postgresql.ENUM('fail_stage', 'fail_overall', 'flag_only', name='criticalaction', create_type=True)
    change_type_enum = postgresql.ENUM('create', 'update', 'delete', 'publish', name='changetype', create_type=True)
    rule_type_enum = postgresql.ENUM('required_step', 'required_phrase', 'forbidden_phrase', 'timing_rule', 'sequence_rule', name='ruletype', create_type=True)
    severity_enum = postgresql.ENUM('critical', 'major', 'minor', name='severity', create_type=True)
    
    # 1. qa_blueprints table
    op.create_table(
        'qa_blueprints',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('company_id', sa.String(36), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', blueprintstatus_enum, nullable=False, server_default='draft'),
        sa.Column('version_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('compiled_flow_version_id', sa.String(36), nullable=True),
        sa.Column('created_by', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('updated_by', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
    )
    
    # Indexes for qa_blueprints
    op.create_index('ix_qa_blueprints_company_id', 'qa_blueprints', ['company_id'])
    op.create_index('ix_qa_blueprints_status', 'qa_blueprints', ['status'])
    op.create_index('ix_qa_blueprints_company_status', 'qa_blueprints', ['company_id', 'status'])
    op.create_index('ix_qa_blueprints_company_name', 'qa_blueprints', ['company_id', 'name'], unique=True)
    
    # GIN index on metadata for search
    op.execute("CREATE INDEX IF NOT EXISTS ix_qa_blueprints_metadata ON qa_blueprints USING GIN (metadata)")
    
    # 2. qa_blueprint_stages table
    op.create_table(
        'qa_blueprint_stages',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('blueprint_id', sa.String(36), sa.ForeignKey('qa_blueprints.id', ondelete='CASCADE'), nullable=False),
        sa.Column('stage_name', sa.String(150), nullable=False),
        sa.Column('ordering_index', sa.Integer(), nullable=False),
        sa.Column('stage_weight', sa.Numeric(5, 2), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Indexes and constraints for qa_blueprint_stages
    op.create_index('ix_qa_blueprint_stages_blueprint_id', 'qa_blueprint_stages', ['blueprint_id'])
    op.create_index('ix_qa_blueprint_stages_ordering', 'qa_blueprint_stages', ['blueprint_id', 'ordering_index'])
    op.create_unique_constraint('uq_blueprint_stage_ordering', 'qa_blueprint_stages', ['blueprint_id', 'ordering_index'])
    op.create_unique_constraint('uq_blueprint_stage_name', 'qa_blueprint_stages', ['blueprint_id', 'stage_name'])
    
    # 3. qa_blueprint_behaviors table
    op.create_table(
        'qa_blueprint_behaviors',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('stage_id', sa.String(36), sa.ForeignKey('qa_blueprint_stages.id', ondelete='CASCADE'), nullable=False),
        sa.Column('behavior_name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('behavior_type', behavior_type_enum, nullable=False, server_default='required'),
        sa.Column('detection_mode', detection_mode_enum, nullable=False, server_default='semantic'),
        sa.Column('phrases', postgresql.JSONB(), nullable=True),
        sa.Column('weight', sa.Numeric(5, 2), nullable=False, server_default='0'),
        sa.Column('critical_action', critical_action_enum, nullable=True),
        sa.Column('ui_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Indexes and constraints for qa_blueprint_behaviors
    op.create_index('ix_qa_blueprint_behaviors_stage_id', 'qa_blueprint_behaviors', ['stage_id'])
    op.create_index('ix_qa_blueprint_behaviors_ui_order', 'qa_blueprint_behaviors', ['stage_id', 'ui_order'])
    op.create_unique_constraint('uq_stage_behavior_name', 'qa_blueprint_behaviors', ['stage_id', 'behavior_name'])
    
    # GIN index on phrases for phrase search
    op.execute("CREATE INDEX IF NOT EXISTS ix_qa_blueprint_behaviors_phrases ON qa_blueprint_behaviors USING GIN (phrases)")
    
    # 4. qa_blueprint_versions table
    op.create_table(
        'qa_blueprint_versions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('blueprint_id', sa.String(36), sa.ForeignKey('qa_blueprints.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('snapshot', postgresql.JSONB(), nullable=False),
        sa.Column('compiled_flow_version_id', sa.String(36), nullable=True),
        sa.Column('published_by', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    
    # Indexes and constraints for qa_blueprint_versions
    op.create_index('ix_qa_blueprint_versions_blueprint_id', 'qa_blueprint_versions', ['blueprint_id'])
    op.create_unique_constraint('uq_blueprint_version', 'qa_blueprint_versions', ['blueprint_id', 'version_number'])
    
    # GIN index on snapshot (use sparingly)
    op.execute("CREATE INDEX IF NOT EXISTS ix_qa_blueprint_versions_snapshot ON qa_blueprint_versions USING GIN (snapshot)")
    
    # 5. qa_blueprint_compiler_map table
    op.create_table(
        'qa_blueprint_compiler_map',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('blueprint_version_id', sa.String(36), sa.ForeignKey('qa_blueprint_versions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('flow_version_id', sa.String(36), nullable=True),
        sa.Column('policy_rules_version_id', sa.String(36), nullable=True),
        sa.Column('rubric_template_id', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    
    # Indexes for qa_blueprint_compiler_map
    op.create_index('ix_qa_blueprint_compiler_map_version_id', 'qa_blueprint_compiler_map', ['blueprint_version_id'])
    
    # 6. qa_blueprint_audit_logs table
    op.create_table(
        'qa_blueprint_audit_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('blueprint_id', sa.String(36), sa.ForeignKey('qa_blueprints.id', ondelete='CASCADE'), nullable=False),
        sa.Column('changed_by', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('change_type', change_type_enum, nullable=False),
        sa.Column('change_summary', sa.Text(), nullable=True),
        sa.Column('change_diff', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    
    # Indexes for qa_blueprint_audit_logs
    op.create_index('ix_qa_blueprint_audit_logs_blueprint_id', 'qa_blueprint_audit_logs', ['blueprint_id'])
    op.create_index('ix_qa_blueprint_audit_logs_created_at', 'qa_blueprint_audit_logs', ['created_at'])
    
    # 7. Compiled artifact tables
    # compiled_flow_versions
    op.create_table(
        'compiled_flow_versions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('company_id', sa.String(36), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('blueprint_version_id', sa.String(36), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('version_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('language', sa.String(10), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    op.create_index('ix_compiled_flow_versions_company_id', 'compiled_flow_versions', ['company_id'])
    op.create_index('ix_compiled_flow_versions_is_active', 'compiled_flow_versions', ['is_active'])
    op.create_index('ix_compiled_flow_versions_blueprint_version_id', 'compiled_flow_versions', ['blueprint_version_id'])
    
    # compiled_flow_stages
    op.create_table(
        'compiled_flow_stages',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('flow_version_id', sa.String(36), sa.ForeignKey('compiled_flow_versions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('ordering_index', sa.Integer(), nullable=False),
        sa.Column('stage_weight', postgresql.JSONB(), nullable=True),
        sa.Column('expected_duration_hint', sa.Integer(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    op.create_index('ix_compiled_flow_stages_flow_version_id', 'compiled_flow_stages', ['flow_version_id'])
    op.create_index('ix_compiled_flow_stages_ordering', 'compiled_flow_stages', ['flow_version_id', 'ordering_index'])
    
    # compiled_flow_steps
    op.create_table(
        'compiled_flow_steps',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('stage_id', sa.String(36), sa.ForeignKey('compiled_flow_stages.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('ordering_index', sa.Integer(), nullable=False),
        sa.Column('expected_role', sa.String(50), nullable=False, server_default='agent'),
        sa.Column('expected_phrases', postgresql.JSONB(), nullable=True),
        sa.Column('detection_hint', sa.String(50), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    op.create_index('ix_compiled_flow_steps_stage_id', 'compiled_flow_steps', ['stage_id'])
    op.create_index('ix_compiled_flow_steps_ordering', 'compiled_flow_steps', ['stage_id', 'ordering_index'])
    
    # compiled_compliance_rules
    op.create_table(
        'compiled_compliance_rules',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('flow_version_id', sa.String(36), sa.ForeignKey('compiled_flow_versions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('flow_step_id', sa.String(36), sa.ForeignKey('compiled_flow_steps.id', ondelete='CASCADE'), nullable=True),
        sa.Column('rule_type', rule_type_enum, nullable=False),
        sa.Column('target', sa.String(36), nullable=True),
        sa.Column('phrases', postgresql.JSONB(), nullable=True),
        sa.Column('match_mode', sa.String(50), nullable=True),
        sa.Column('severity', severity_enum, nullable=False, server_default='major'),
        sa.Column('action_on_fail', sa.String(50), nullable=True),
        sa.Column('timing_constraints', postgresql.JSONB(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    op.create_index('ix_compiled_compliance_rules_flow_version_id', 'compiled_compliance_rules', ['flow_version_id'])
    op.create_index('ix_compiled_compliance_rules_flow_step_id', 'compiled_compliance_rules', ['flow_step_id'])
    
    # compiled_rubric_templates
    op.create_table(
        'compiled_rubric_templates',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('flow_version_id', sa.String(36), sa.ForeignKey('compiled_flow_versions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('categories', postgresql.JSONB(), nullable=False),
        sa.Column('mappings', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    op.create_index('ix_compiled_rubric_templates_flow_version_id', 'compiled_rubric_templates', ['flow_version_id'])
    
    # 8. Sandbox tables
    sandbox_run_status_enum = postgresql.ENUM('queued', 'running', 'succeeded', 'failed', 'canceled', name='sandboxrunstatus', create_type=True)
    sandbox_input_type_enum = postgresql.ENUM('transcript', 'audio', name='sandboxinputtype', create_type=True)
    
    # sandbox_runs
    op.create_table(
        'sandbox_runs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('company_id', sa.String(36), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('created_by', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('blueprint_id', sa.String(36), sa.ForeignKey('qa_blueprints.id'), nullable=True),
        sa.Column('blueprint_version_id', sa.String(36), sa.ForeignKey('qa_blueprint_versions.id'), nullable=True),
        sa.Column('input_type', sandbox_input_type_enum, nullable=False),
        sa.Column('input_location', sa.String(500), nullable=True),
        sa.Column('status', sandbox_run_status_enum, nullable=False, server_default='queued'),
        sa.Column('result_id', sa.String(36), nullable=True),
        sa.Column('idempotency_key', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    op.create_index('ix_sandbox_runs_company_id', 'sandbox_runs', ['company_id'])
    op.create_index('ix_sandbox_runs_status', 'sandbox_runs', ['status'])
    op.create_index('ix_sandbox_runs_blueprint_id', 'sandbox_runs', ['blueprint_id'])
    op.create_index('ix_sandbox_runs_idempotency_key', 'sandbox_runs', ['idempotency_key'])
    op.create_index('ix_sandbox_runs_created_at', 'sandbox_runs', ['created_at'])
    
    # sandbox_results
    op.create_table(
        'sandbox_results',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('sandbox_run_id', sa.String(36), nullable=False, unique=True),
        sa.Column('transcript_snapshot', postgresql.JSONB(), nullable=True),
        sa.Column('detection_output', postgresql.JSONB(), nullable=True),
        sa.Column('llm_stage_outputs', postgresql.JSONB(), nullable=True),
        sa.Column('final_evaluation', postgresql.JSONB(), nullable=True),
        sa.Column('logs', postgresql.JSONB(), nullable=True),
        sa.Column('cost_estimate', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    
    op.create_foreign_key(
        'fk_sandbox_results_run',
        'sandbox_results',
        'sandbox_runs',
        ['sandbox_run_id'],
        ['id']
    )
    op.create_index('ix_sandbox_results_run_id', 'sandbox_results', ['sandbox_run_id'])
    
    # sandbox_quota
    op.create_table(
        'sandbox_quota',
        sa.Column('company_id', sa.String(36), sa.ForeignKey('companies.id'), primary_key=True),
        sa.Column('monthly_allowed_runs', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('monthly_used_runs', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_reset', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    
    # 9. New evaluations table (Blueprint-based)
    evaluationstatus_enum = postgresql.ENUM('pending', 'completed', 'reviewed', 'failed', name='evaluationstatus', create_type=True)
    
    op.create_table(
        'evaluations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('recording_id', sa.String(36), sa.ForeignKey('recordings.id'), nullable=False, unique=True),
        sa.Column('company_id', sa.String(36), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('blueprint_id', sa.String(36), sa.ForeignKey('qa_blueprints.id'), nullable=True),
        sa.Column('blueprint_version_id', sa.String(36), sa.ForeignKey('qa_blueprint_versions.id'), nullable=True),
        sa.Column('compiled_flow_version_id', sa.String(36), sa.ForeignKey('compiled_flow_versions.id'), nullable=True),
        sa.Column('overall_score', sa.Integer(), nullable=False),
        sa.Column('overall_passed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('requires_human_review', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('deterministic_results', postgresql.JSONB(), nullable=True),
        sa.Column('llm_stage_evaluations', postgresql.JSONB(), nullable=True),
        sa.Column('final_evaluation', postgresql.JSONB(), nullable=True),
        sa.Column('status', evaluationstatus_enum, nullable=False, server_default='pending'),
        sa.Column('evaluated_by_user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('agent_id', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('team_id', sa.String(36), sa.ForeignKey('teams.id'), nullable=True),
        sa.Column('prompt_version', sa.String(20), nullable=True),
        sa.Column('model_version', sa.String(50), nullable=True),
        sa.Column('model_temperature', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('evaluation_seed', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    op.create_index('ix_evaluations_recording_id', 'evaluations', ['recording_id'])
    op.create_index('ix_evaluations_company_id', 'evaluations', ['company_id'])
    op.create_index('ix_evaluations_blueprint_id', 'evaluations', ['blueprint_id'])
    op.create_index('ix_evaluations_compiled_flow_version_id', 'evaluations', ['compiled_flow_version_id'])
    op.create_index('ix_evaluations_status', 'evaluations', ['status'])
    op.create_index('ix_evaluations_created_at', 'evaluations', ['created_at'])
    op.create_index('ix_evaluations_agent_id', 'evaluations', ['agent_id'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('evaluations')
    op.drop_table('sandbox_quota')
    op.drop_table('sandbox_results')
    op.drop_table('sandbox_runs')
    op.drop_table('compiled_rubric_templates')
    op.drop_table('compiled_compliance_rules')
    op.drop_table('compiled_flow_steps')
    op.drop_table('compiled_flow_stages')
    op.drop_table('compiled_flow_versions')
    op.drop_table('qa_blueprint_audit_logs')
    op.drop_table('qa_blueprint_compiler_map')
    op.drop_table('qa_blueprint_versions')
    op.drop_table('qa_blueprint_behaviors')
    op.drop_table('qa_blueprint_stages')
    op.drop_table('qa_blueprints')
    
    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS evaluationstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS sandboxrunstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS sandboxinputtype CASCADE")
    op.execute("DROP TYPE IF EXISTS blueprintstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS behaviortype CASCADE")
    op.execute("DROP TYPE IF EXISTS detectionmode CASCADE")
    op.execute("DROP TYPE IF EXISTS criticalaction CASCADE")
    op.execute("DROP TYPE IF EXISTS changetype CASCADE")
    op.execute("DROP TYPE IF EXISTS ruletype CASCADE")
    op.execute("DROP TYPE IF EXISTS severity CASCADE")

