import requests
import json

# Try to get flow versions from the API
try:
    # Assuming the backend is running on localhost:8000
    response = requests.get('http://localhost:8000/api/flow-versions', timeout=5)
    if response.status_code == 200:
        flow_versions = response.json()
        print(f'Found {len(flow_versions)} flow versions:')
        print('=' * 50)

        for fv in flow_versions:
            print(f'Flow Version: {fv["name"]} (ID: {fv["id"]})')
            total_steps = 0
            required_steps_without_phrases = 0

            for stage in sorted(fv['stages'], key=lambda s: s['order']):
                print(f'  Stage: {stage["name"]}')
                for step in sorted(stage['steps'], key=lambda s: s['order']):
                    total_steps += 1
                    phrases = step.get('expected_phrases', []) or []
                    status = '✓' if phrases else '✗'
                    print(f'    {status} Step: {step["name"]} (Required: {step["required"]}, Expected Phrases: {len(phrases)})')

                    if step['required'] and not phrases:
                        required_steps_without_phrases += 1

                    if phrases:
                        for phrase in phrases[:2]:  # Show first 2 phrases
                            print(f'        - "{phrase}"')
                        if len(phrases) > 2:
                            print(f'        - ... and {len(phrases) - 2} more')
            print(f'  Summary: {total_steps} total steps, {required_steps_without_phrases} required steps missing phrases')
            print()
    else:
        print(f'API returned status {response.status_code}')
except Exception as e:
    print(f'Could not connect to API: {e}')
    print('Make sure the backend server is running on localhost:8000')
