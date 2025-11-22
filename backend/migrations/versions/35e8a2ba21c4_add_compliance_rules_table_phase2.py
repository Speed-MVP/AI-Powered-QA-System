"""add_compliance_rules_table_phase2

Revision ID: 35e8a2ba21c4
Revises: fec00aff39a6
Create Date: 2025-11-22 23:14:49.323683

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '35e8a2ba21c4'
down_revision = 'fec00aff39a6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ENUM types for rule_type and severity
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE ruletype AS ENUM ('required_phrase', 'forbidden_phrase', 'sequence_rule', 'timing_rule', 'verification_rule', 'conditional_rule');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE severity AS ENUM ('critical', 'major', 'minor');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Create compliance_rules table
    op.create_table(
        'compliance_rules',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('flow_version_id', sa.String(36), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('severity', sa.Enum('critical', 'major', 'minor', name='severity'), nullable=False),
        sa.Column('rule_type', sa.Enum('required_phrase', 'forbidden_phrase', 'sequence_rule', 'timing_rule', 'verification_rule', 'conditional_rule', name='ruletype'), nullable=False),
        sa.Column('applies_to_stages', postgresql.JSONB(), nullable=True),
        sa.Column('params', postgresql.JSONB(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    
    # Create foreign key
    op.create_foreign_key(
        'fk_compliance_rules_flow_version',
        'compliance_rules',
        'flow_versions',
        ['flow_version_id'],
        ['id'],
        ondelete='CASCADE'
    )
    
    # Create indexes
    op.create_index('ix_compliance_rules_flow_version_id', 'compliance_rules', ['flow_version_id'])
    op.create_index('ix_compliance_rules_active', 'compliance_rules', ['active'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_compliance_rules_active', 'compliance_rules')
    op.drop_index('ix_compliance_rules_flow_version_id', 'compliance_rules')
    
    # Drop foreign key
    op.drop_constraint('fk_compliance_rules_flow_version', 'compliance_rules', type_='foreignkey')
    
    # Drop table
    op.drop_table('compliance_rules')
    
    # Drop ENUM types
    op.execute('DROP TYPE IF EXISTS ruletype')
    op.execute('DROP TYPE IF EXISTS severity')

