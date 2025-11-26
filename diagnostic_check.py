import sys
sys.path.append('backend')
from backend.app.database import SessionLocal
from backend.app.models.recording import Recording
from backend.app.models.transcript import Transcript
from backend.app.models.evaluation import Evaluation

db = SessionLocal()
try:
    # Check the recording from the user's JSON
    recording_id = '3d57771e-36f4-4fcc-b164-7fcd2ab1b553'

    recording = db.query(Recording).filter(Recording.id == recording_id).first()
    if recording:
        transcript = db.query(Transcript).filter(Transcript.recording_id == recording_id).first()
        evaluation = db.query(Evaluation).filter(Evaluation.recording_id == recording_id).order_by(Evaluation.created_at.desc()).first()

        print('=== RECORDING INFO ===')
        print(f'ID: {recording.id}')
        print(f'Status: {recording.status}')
        print(f'Created: {recording.created_at}')
        print(f'Processed: {recording.processed_at}')

        print('\n=== TRANSCRIPT INFO ===')
        if transcript:
            print(f'Transcript exists: YES')
            print(f'Transcript length: {len(transcript.transcript_text or "")}')
            print(f'Normalized length: {len(transcript.normalized_text or "")}')
            print(f'Created: {transcript.created_at}')
            print(f'Preview: {(transcript.normalized_text or transcript.transcript_text or "")[:200]}...')
        else:
            print('Transcript exists: NO')

        print('\n=== EVALUATION INFO ===')
        if evaluation:
            print(f'Evaluation exists: YES')
            print(f'Evaluation ID: {evaluation.id}')
            print(f'Overall Score: {evaluation.overall_score}')
            print(f'Created: {evaluation.created_at}')
            print(f'Requires human review: {evaluation.requires_human_review}')

            # Check timing
            if transcript and evaluation:
                transcript_before_eval = transcript.created_at < evaluation.created_at
                print(f'Transcript created BEFORE evaluation: {transcript_before_eval}')
        else:
            print('Evaluation exists: NO')

    # Check recent evaluations for this recording
    print('\n=== RECENT EVALUATIONS ===')
    evaluations = db.query(Evaluation).filter(Evaluation.recording_id == recording_id).order_by(Evaluation.created_at.desc()).limit(5).all()
    for i, eval in enumerate(evaluations):
        print(f'{i+1}. {eval.id} - Score: {eval.overall_score} - Created: {eval.created_at}')

finally:
    db.close()
