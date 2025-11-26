import os
import sys
sys.path.append('backend')

# Set minimal environment
os.environ.setdefault('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/qa_system')
os.environ.setdefault('GCP_PROJECT_ID', 'dummy')
os.environ.setdefault('GCP_BUCKET_NAME', 'dummy')
os.environ.setdefault('JWT_SECRET', 'dummy')
os.environ.setdefault('DEEPGRAM_API_KEY', 'dummy')
os.environ.setdefault('SMTP_HOST', 'dummy')
os.environ.setdefault('SMTP_USER', 'dummy')
os.environ.setdefault('SMTP_PASSWORD', 'dummy')
os.environ.setdefault('SMTP_FROM', 'dummy')

from backend.app.database import SessionLocal
from backend.app.models.compliance_rule import ComplianceRule

db = SessionLocal()
try:
    # Check the Forbidden PII rule
    rule_id = 'b7a91c4e-8c1f-42f5-9130-22b6d4c28290'

    rule = db.query(ComplianceRule).filter(ComplianceRule.id == rule_id).first()
    if rule:
        print('=== FORBIDDEN PII RULE ===')
        print(f'ID: {rule.id}')
        print(f'Name: {rule.name}')
        print(f'Rule Type: {rule.rule_type}')
        print(f'Pattern: {rule.pattern}')
        print(f'Severity: {rule.severity}')
        print(f'Active: {rule.active}')
        print(f'Flow Version: {rule.flow_version_id}')
    else:
        print(f'Rule {rule_id} not found')

    # Check all forbidden rules
    print('\n=== ALL FORBIDDEN RULES ===')
    forbidden_rules = db.query(ComplianceRule).filter(ComplianceRule.rule_type == 'forbidden_phrase').all()
    for rule in forbidden_rules:
        print(f'{rule.id}: {rule.name} - Pattern: {rule.pattern}')

finally:
    db.close()
