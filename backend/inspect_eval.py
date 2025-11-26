import sys
import os
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.evaluation import Evaluation

def inspect_eval():
    recording_id = 'b8bc90fd-bd95-4c14-a2f0-6569b25dc6aa'
    db = SessionLocal()
    eval = db.query(Evaluation).filter(Evaluation.recording_id == recording_id).first()
    if eval:
        print(f"Overall Score: {eval.overall_score}")
        violations = eval.final_evaluation.get("policy_violations", [])
        print(f"Violations Count: {len(violations)}")
        for v in violations:
            print(f"- {v.get('description')} (Severity: {v.get('severity')})")
            
        # Also check deterministic results to see if step_results have timestamps
        det_results = eval.deterministic_results
        if det_results:
            print("\nDeterministic Results (Sample):")
            # det_results is a dict, maybe stage_results inside
            # Check keys
            print(f"Keys: {list(det_results.keys())}")
            if "stage_results" in det_results:
                pass # complex structure
            
        # Check llm_stage_evaluations
        print("\nLLM Stage Evaluations:")
        llm_evals = eval.llm_stage_evaluations
        for stage_id, stage_data in llm_evals.items():
             print(f"Stage {stage_data.get('stage_name')}: Score {stage_data.get('stage_score')}")
             for b in stage_data.get("behaviors", []):
                 print(f"  - {b.get('behavior_name')}: {b.get('satisfaction_level')} (Conf: {b.get('confidence')})")

    db.close()

if __name__ == "__main__":
    inspect_eval()
