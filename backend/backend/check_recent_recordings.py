import sys
import os
from sqlalchemy import text

# Add current directory to path so we can import app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.recording import Recording, RecordingStatus
from app.models.evaluation import Evaluation

def check_recent_recordings():
    db = SessionLocal()
    try:
        print("Checking recent 5 recordings:")
        recordings = db.query(Recording).order_by(Recording.uploaded_at.desc()).limit(5).all()
        
        for r in recordings:
            print(f"Recording: {r.id}")
            print(f"  File: {r.file_name}")
            print(f"  Status: {r.status}")
            print(f"  Uploaded At: {r.uploaded_at}")
            print(f"  Error Message: {r.error_message}")
            
            evaluation = db.query(Evaluation).filter(Evaluation.recording_id == r.id).first()
            if evaluation:
                print(f"  Evaluation: {evaluation.id} ({evaluation.status})")
                print(f"  Score: {evaluation.overall_score}")
            else:
                print("  Evaluation: NOT FOUND")
            print("-" * 30)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_recent_recordings()
