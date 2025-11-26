"""
Evaluation API Routes - Phase 9
Endpoints for Blueprint-based evaluations
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.database import get_db
from app.models.user import User
from app.models.evaluation import Evaluation
from app.models.recording import Recording, RecordingStatus
from app.models.transcript import Transcript
from app.middleware.auth import get_current_user
from app.middleware.permissions import require_company_access
from app.services.cloud_tasks import cloud_tasks_service
from app.tasks.process_recording_blueprint import process_recording_blueprint_task

logger = logging.getLogger(__name__)
router = APIRouter(tags=["evaluations"])


@router.get("/{id}")
async def get_evaluation(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get evaluation by evaluation_id or recording_id"""
    # Try as evaluation_id first
    evaluation = db.query(Evaluation).filter(
        Evaluation.id == id
    ).first()
    
    # If not found, try as recording_id
    if not evaluation:
        evaluation = db.query(Evaluation).filter(
            Evaluation.recording_id == id
        ).first()
    
    if not evaluation:
        # Check if it was a recording ID and if the recording exists
        recording = db.query(Recording).filter(Recording.id == id).first()
        if recording:
            if recording.status == RecordingStatus.failed:
                # If recording failed, return 400 with error message
                error_msg = recording.error_message or "Processing failed"
                raise HTTPException(status_code=400, detail=f"Recording processing failed: {error_msg}")
            elif recording.status == RecordingStatus.processing:
                raise HTTPException(status_code=404, detail="Evaluation in progress")
            elif recording.status == RecordingStatus.queued:
                raise HTTPException(status_code=404, detail="Recording queued for processing")

        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    require_company_access(evaluation.company_id, current_user)
    
    # Retrieve transcript (simplified flow)
    transcript = db.query(Transcript).filter(
        Transcript.recording_id == evaluation.recording_id
    ).first()
    
    transcript_data = None
    if transcript:
        transcript_data = {
            "id": transcript.id,
            "text": transcript.transcript_text,
            "segments": transcript.diarized_segments,
            "sentiment": transcript.sentiment_analysis,
            "confidence": transcript.transcription_confidence
        }
    
    return {
        "evaluation_id": evaluation.id,
        "recording_id": evaluation.recording_id,
        "blueprint_id": evaluation.blueprint_id,
        "overall_score": evaluation.overall_score,
        "overall_passed": evaluation.overall_passed,
        "requires_human_review": evaluation.requires_human_review,
        "confidence_score": evaluation.confidence_score,
        "stage_scores": evaluation.final_evaluation.get("stage_scores", []) if evaluation.final_evaluation else [],
        "policy_violations": evaluation.final_evaluation.get("policy_violations", []) if evaluation.final_evaluation else [],
        "created_at": evaluation.created_at.isoformat(),
        "status": evaluation.status.value,
        "transcript": transcript_data
    }


@router.get("/{id}/transcript")
async def get_evaluation_transcript(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get transcript for an evaluation/recording"""
    # Try as evaluation_id first
    evaluation = db.query(Evaluation).filter(
        Evaluation.id == id
    ).first()
    
    recording_id = None
    company_id = None
    
    if evaluation:
        recording_id = evaluation.recording_id
        company_id = evaluation.company_id
    else:
        # Try as recording_id
        recording = db.query(Recording).filter(
            Recording.id == id
        ).first()
        
        if recording:
            recording_id = recording.id
            company_id = recording.company_id
        else:
            raise HTTPException(status_code=404, detail="Evaluation or recording not found")
            
    require_company_access(company_id, current_user)
    
    transcript = db.query(Transcript).filter(
        Transcript.recording_id == recording_id
    ).first()
    
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
        
    # Align response shape with frontend expectations (api.getTranscript)
    # while keeping extras for future use.
    return {
        "id": transcript.id,
        "recording_id": transcript.recording_id,
        # Primary fields expected by web client
        "transcript_text": transcript.transcript_text,
        "diarized_segments": transcript.diarized_segments,
        "confidence": transcript.transcription_confidence,
        # Additional metadata (not currently used by web client but useful)
        "sentiment": transcript.sentiment_analysis,
    }


@router.post("/recordings/{recording_id}/evaluate")
async def trigger_evaluation(
    recording_id: str,
    blueprint_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """Trigger evaluation for a recording"""
    recording = db.query(Recording).filter(
        Recording.id == recording_id
    ).first()
    
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    require_company_access(recording.company_id, current_user)
    
    # Enqueue evaluation task
    payload = {
        "recording_id": recording_id,
        "blueprint_id": blueprint_id
    }
    
    # For now, run synchronously (in production, would use Cloud Tasks)
    # TODO: Use Cloud Tasks for async processing
    result = await process_recording_blueprint_task(payload)
    
    if result.get("status") == "failed":
        raise HTTPException(status_code=500, detail=result.get("error", "Evaluation failed"))
    
    return {
        "evaluation_id": result.get("evaluation_id"),
        "overall_score": result.get("overall_score"),
        "overall_passed": result.get("overall_passed"),
        "status": "completed"
    }
