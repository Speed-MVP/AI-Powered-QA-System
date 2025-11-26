import sys
import os
import json

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.transcript import Transcript
from app.models.recording import Recording
from app.models.compiled_artifacts import RuleType

def check_data():
    db = SessionLocal()
    try:
        rec_id = 'b8bc90fd-bd95-4c14-a2f0-6569b25dc6aa'
        print(f"Checking recording {rec_id}...")
        
        transcript = db.query(Transcript).filter(Transcript.recording_id == rec_id).first()
        if transcript:
            print(f"Transcript found: {transcript.id}")
            print(f"FULL TRANSCRIPT:\n{transcript.transcript_text}")
        else:
            print("Transcript NOT found!")
            
        # Also check the compliance rules logic simulation
        print("\n--- Simulation Compliance Logic ---")
        # Simulate the inputs that EvaluationPipeline sends to DeterministicRuleEngine
        
        # Case: Semantic step detected by LLM but NO phrases matched deterministically
        step_id = "step_123"
        
        # stage_results constructed in EvaluationPipeline
        stage_results = {
            "stage_1": {
                "step_results": [
                    {
                        "step_id": step_id,
                        "step_name": "Semantic Step",
                        "detected": True, # LLM says True
                        "timestamp": None # No phrase match -> No timestamp
                    }
                ]
            }
        }
        
        step_timestamps = {}
        for stage_id, results in stage_results.items():
            for step_result in results.get("step_results", []):
                if step_result.get("timestamp"):
                    step_timestamps[step_result["step_id"]] = step_result["timestamp"]
        
        print(f"step_timestamps: {step_timestamps}")
        
        # Rule checking logic
        target_step_id = step_id
        passed = False
        if target_step_id and target_step_id in step_timestamps:
            passed = True
            
        print(f"Rule check for step {step_id}: {'PASSED' if passed else 'FAILED'}")
        if not passed:
            print("Reason: step_id not in step_timestamps (because timestamp is None)")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_data()
