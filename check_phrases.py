import os
import sys
sys.path.append('backend')

# Set minimal environment for import
os.environ.setdefault('DATABASE_URL', 'dummy')
os.environ.setdefault('GCP_PROJECT_ID', 'dummy')
os.environ.setdefault('GCP_BUCKET_NAME', 'dummy')
os.environ.setdefault('JWT_SECRET', 'dummy')
os.environ.setdefault('DEEPGRAM_API_KEY', 'dummy')
os.environ.setdefault('SMTP_HOST', 'dummy')
os.environ.setdefault('SMTP_USER', 'dummy')
os.environ.setdefault('SMTP_PASSWORD', 'dummy')
os.environ.setdefault('SMTP_FROM', 'dummy')

try:
    from backend.app.database import SessionLocal
    from backend.app.models.flow_step import FlowStep

    db = SessionLocal()

    # Get steps from the flow version mentioned in the JSON
    flow_version_id = '347999ac-26b8-4f43-bc98-3e99121d8cda'

    print('=== CONFIGURED EXPECTED PHRASES ===')
    steps = db.query(FlowStep).join(FlowStep.stage).filter(FlowStep.stage.has(flow_version_id=flow_version_id)).all()

    total_steps = len(steps)
    configured_steps = 0
    required_configured = 0
    required_total = 0

    for step in sorted(steps, key=lambda s: (s.stage.order, s.order)):
        phrases = step.expected_phrases or []
        if phrases:
            configured_steps += 1
        if step.required:
            required_total += 1
            if phrases:
                required_configured += 1

        status = '✅' if phrases else '❌'
        required = 'REQUIRED' if step.required else 'optional'

        print(f'{status} {step.stage.name} → {step.name} ({required})')
        if phrases:
            for i, phrase in enumerate(phrases[:3]):  # Show first 3
                print(f'   {i+1}. "{phrase}"')
            if len(phrases) > 3:
                print(f'   ... and {len(phrases) - 3} more')
        else:
            print('   NO PHRASES CONFIGURED')
        print()

    print('=== SUMMARY ===')
    print(f'Total steps: {total_steps}')
    print(f'Steps with phrases: {configured_steps}/{total_steps}')
    print(f'Required steps with phrases: {required_configured}/{required_total}')

finally:
    db.close()
