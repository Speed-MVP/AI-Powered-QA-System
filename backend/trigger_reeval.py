import sys
import os
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.tasks.process_recording_blueprint import process_recording_blueprint_task
from app.models.evaluation import Evaluation

async def reevaluate():
    recording_id = 'b8bc90fd-bd95-4c14-a2f0-6569b25dc6aa'
    print(f"Triggering re-evaluation for {recording_id}...")
    
    try:
        result = await process_recording_blueprint_task({"recording_id": recording_id})
        print(f"Re-evaluation result: {result}")
        
        # Check new score
        db = SessionLocal()
        eval = db.query(Evaluation).filter(Evaluation.recording_id == recording_id).first()
        if eval:
            print(f"New Overall Score: {eval.overall_score}")
            print(f"Passed: {eval.overall_passed}")
            print(f"Violations: {len(eval.policy_violations) if eval.policy_violations else 0}")
        db.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(reevaluate())
