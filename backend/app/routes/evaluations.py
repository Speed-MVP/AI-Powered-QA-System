"""
Evaluation API Routes - Phase 9
Endpoints for Blueprint-based evaluations
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.database import get_db
from app.models.user import User
from app.models.evaluation import Evaluation, EvaluationStatus
from app.models.recording import Recording, RecordingStatus
from app.models.transcript import Transcript
from app.models.qa_blueprint import QABlueprint, BlueprintStatus
from app.middleware.auth import get_current_user
from app.middleware.permissions import require_company_access
from app.services.cloud_tasks import cloud_tasks_service
from app.tasks.process_recording_blueprint import process_recording_blueprint_task

logger = logging.getLogger(__name__)
router = APIRouter(tags=["evaluations"])


@router.get("/{evaluation_id}")
async def get_evaluation(
    evaluation_id: str,
    include_explanation: bool = Query(
        False,
        description="Include detailed explanation and confidence breakdown in response",
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get evaluation by evaluation_id (no recording_id fallback)"""
    evaluation = db.query(Evaluation).filter(
        Evaluation.id == evaluation_id
    ).first()
    
    if not evaluation:
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
    
    response = {
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

    # Optionally include explanation and confidence breakdown from final_evaluation
    if include_explanation and evaluation.final_evaluation:
        explanation = evaluation.final_evaluation.get("explanation")
        confidence_breakdown = evaluation.final_evaluation.get("confidence_breakdown")
        if explanation is not None:
            response["explanation"] = explanation
        if confidence_breakdown is not None:
            response["confidence_breakdown"] = confidence_breakdown

    return response


@router.get("/{evaluation_id}/transcript")
async def get_evaluation_transcript(
    evaluation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get transcript for an evaluation (no recording_id fallback)"""
    evaluation = db.query(Evaluation).filter(
        Evaluation.id == evaluation_id
    ).first()
    
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
            
    require_company_access(evaluation.company_id, current_user)
    
    transcript = db.query(Transcript).filter(
        Transcript.recording_id == evaluation.recording_id
    ).first()
    
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
        
    return {
        "id": transcript.id,
        "recording_id": transcript.recording_id,
        "transcript_text": transcript.transcript_text,
        "diarized_segments": transcript.diarized_segments,
        "confidence": transcript.transcription_confidence,
        "sentiment": transcript.sentiment_analysis,
    }


@router.post("/recordings/{recording_id}/evaluate")
async def trigger_evaluation(
    recording_id: str,
    blueprint_id: str,
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
    
    # Avoid duplicate or conflicting processing
    if recording.status in {RecordingStatus.processing, RecordingStatus.queued, RecordingStatus.failed}:
        raise HTTPException(
            status_code=409,
            detail=f"Recording is currently {recording.status.value}"
        )
    
    require_company_access(recording.company_id, current_user)

    existing_evaluation = db.query(Evaluation).filter(
        Evaluation.recording_id == recording_id
    ).first()

    # If already completed, return existing result to keep the flow idempotent
    if existing_evaluation:
        if existing_evaluation.status in {EvaluationStatus.completed, EvaluationStatus.reviewed}:
            return {
                "evaluation_id": existing_evaluation.id,
                "overall_score": existing_evaluation.overall_score,
                "overall_passed": existing_evaluation.overall_passed,
                "confidence_score": existing_evaluation.confidence_score,
                "status": existing_evaluation.status.value
            }
        if existing_evaluation.status == EvaluationStatus.pending:
            raise HTTPException(status_code=409, detail="Evaluation already in progress")
        if existing_evaluation.status == EvaluationStatus.failed:
            raise HTTPException(status_code=409, detail="Existing evaluation failed; please retry after resolving issues")

    # Validate requested blueprint (required)
    blueprint = db.query(QABlueprint).filter(QABlueprint.id == blueprint_id).first()
    if not blueprint or blueprint.status != BlueprintStatus.published:
        raise HTTPException(status_code=400, detail="Blueprint not found or not published")
    if blueprint.company_id != recording.company_id:
        raise HTTPException(status_code=403, detail="Blueprint does not belong to this company")
    
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
        "confidence_score": result.get("confidence_score"),
        "status": result.get("status", "completed")
    }
