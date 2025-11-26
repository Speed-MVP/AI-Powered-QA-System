import sys
sys.path.append('backend')
from backend.app.database import SessionLocal
from backend.app.models.transcript import Transcript

db = SessionLocal()
try:
    transcripts = db.query(Transcript).all()
    print(f'Found {len(transcripts)} transcripts in database:')
    print('=' * 60)

    empty_count = 0
    for t in transcripts:
        text_len = len(t.transcript_text or '')
        normalized_len = len(t.normalized_text or '')
        segments_count = len(t.diarized_segments or [])

        if text_len == 0 and normalized_len == 0:
            empty_count += 1
            print(f'❌ EMPTY: Recording {t.recording_id[:8]}...')
            print(f'   transcript_text: {text_len} chars')
            print(f'   normalized_text: {normalized_len} chars')
            print(f'   segments: {segments_count}')
        else:
            print(f'✅ OK: Recording {t.recording_id[:8]}... ({text_len + normalized_len} chars, {segments_count} segments)')

    print(f'\nSummary: {empty_count} empty transcripts out of {len(transcripts)} total')

finally:
    db.close()
