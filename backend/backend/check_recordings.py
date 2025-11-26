import sys
import os
import datetime

# Add current directory to path so we can import app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.recording import Recording, RecordingStatus
from app.models.evaluation import Evaluation

def check_recordings():
    db = SessionLocal()
    try:
        # Get recent recordings
        recordings = db.query(Recording).order_by(Recording.uploaded_at.desc()).limit(5).all()
        print(f"Found {len(recordings)} recent recordings.")
        
        for rec in recordings:
            print(f"\nRecording: {rec.id}")
            print(f"  File: {rec.file_name}")
            print(f"  Status: {rec.status}")
            print(f"  Created At: {rec.uploaded_at}")
            
            # Check evaluation
            evaluation = db.query(Evaluation).filter(Evaluation.recording_id == rec.id).first()
            if evaluation:
                print(f"  Evaluation: {evaluation.id}")
                print(f"  Eval Status: {evaluation.status}")
                print(f"  Score: {evaluation.overall_score}")
            else:
                print(f"  Evaluation: NONE")
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_recordings()
