from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.evaluation import Evaluation
from app.models.recording import Recording
from app.middleware.auth import get_current_user
from app.schemas.evaluation import EvaluationResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/{recording_id}", response_model=EvaluationResponse)
async def get_evaluation(
    recording_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get evaluation results for a recording"""
    # First verify the recording belongs to the user's company
    recording = db.query(Recording).filter(
        Recording.id == recording_id,
        Recording.company_id == current_user.company_id
    ).first()
    
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    # Get evaluation
    evaluation = db.query(Evaluation).filter(
        Evaluation.recording_id == recording_id
    ).first()
    
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    # Convert customer_tone JSONB to dict if it exists
    evaluation_dict = {
        "id": evaluation.id,
        "recording_id": evaluation.recording_id,
        "flow_version_id": evaluation.flow_version_id,
        "rubric_template_id": evaluation.rubric_template_id,
        "overall_score": evaluation.overall_score,
        "resolution_detected": evaluation.resolution_detected,
        "resolution_confidence": evaluation.resolution_confidence,
        "customer_tone": evaluation.customer_tone if evaluation.customer_tone else None,
        "llm_analysis": evaluation.llm_analysis,
        "status": evaluation.status.value,
        "created_at": evaluation.created_at,
        "category_scores": [
            {
                "id": score.id,
                "category_name": score.category_name,
                "score": score.score,
                "feedback": score.feedback
            }
            for score in evaluation.category_scores
        ]
    }
    
    return evaluation_dict


@router.get("/{evaluation_id}/with-template")
async def get_evaluation_with_template(
    evaluation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get evaluation results with FlowVersion and RubricTemplate details for human review"""
    # Get evaluation
    evaluation = db.query(Evaluation).filter(
        Evaluation.id == evaluation_id
    ).first()

    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    # Verify the recording belongs to the user's company
    recording = db.query(Recording).filter(
        Recording.id == evaluation.recording_id,
        Recording.company_id == current_user.company_id
    ).first()

    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")

    # Get FlowVersion and RubricTemplate (Phase 7 system)
    from app.models.flow_version import FlowVersion
    from app.models.rubric_template import RubricTemplate, RubricCategory
    from sqlalchemy.orm import joinedload

    flow_version = None
    rubric_template = None
    
    if evaluation.flow_version_id:
        flow_version = db.query(FlowVersion).filter(
            FlowVersion.id == evaluation.flow_version_id,
            FlowVersion.company_id == current_user.company_id
        ).first()
    
    if evaluation.rubric_template_id:
        rubric_template = db.query(RubricTemplate).options(
            joinedload(RubricTemplate.categories).joinedload(RubricCategory.mappings)
        ).filter(
            RubricTemplate.id == evaluation.rubric_template_id
        ).first()

    # Convert customer_tone JSONB to dict if it exists
    evaluation_dict = {
        "id": evaluation.id,
        "recording_id": evaluation.recording_id,
        "flow_version_id": evaluation.flow_version_id,
        "rubric_template_id": evaluation.rubric_template_id,
        "overall_score": evaluation.overall_score,
        "resolution_detected": evaluation.resolution_detected,
        "resolution_confidence": evaluation.resolution_confidence,
        "customer_tone": evaluation.customer_tone if evaluation.customer_tone else None,
        "llm_analysis": evaluation.llm_analysis,
        "status": evaluation.status.value,
        "created_at": evaluation.created_at,
        "category_scores": [
            {
                "id": score.id,
                "category_name": score.category_name,
                "score": score.score,
                "feedback": score.feedback
            }
            for score in evaluation.category_scores
        ],
        "flow_version": {
            "id": flow_version.id,
            "name": flow_version.name,
            "description": flow_version.description,
            "stages": [
                {
                    "id": stage.id,
                    "name": stage.name,
                    "order": stage.order,
                    "steps": [
                        {
                            "id": step.id,
                            "name": step.name,
                            "description": step.description,
                            "required": step.required,
                            "order": step.order
                        }
                        for step in sorted(stage.steps, key=lambda x: x.order)
                    ]
                }
                for stage in sorted(flow_version.stages, key=lambda x: x.order)
            ] if flow_version else []
        },
        "rubric_template": {
            "id": rubric_template.id,
            "name": rubric_template.name,
            "description": rubric_template.description,
            "categories": [
                {
                    "id": category.id,
                    "name": category.name,
                    "description": category.description,
                    "weight": float(category.weight),
                    "pass_threshold": category.pass_threshold,
                    "level_definitions": category.level_definitions
                }
                for category in rubric_template.categories
            ] if rubric_template else []
        }
    }

    return evaluation_dict


@router.get("/{recording_id}/transcript")
async def get_transcript(
    recording_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get transcript for a recording"""
    from app.models.transcript import Transcript
    
    # First verify the recording belongs to the user's company
    recording = db.query(Recording).filter(
        Recording.id == recording_id,
        Recording.company_id == current_user.company_id
    ).first()
    
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    # Get transcript
    transcript = db.query(Transcript).filter(
        Transcript.recording_id == recording_id
    ).first()
    
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
    
    return {
        "recording_id": recording_id,
        "transcript_text": transcript.transcript_text,
        "diarized_segments": transcript.diarized_segments,
        "confidence": float(transcript.transcription_confidence) if transcript.transcription_confidence else None
    }


@router.get("/{evaluation_id}/scores")
async def get_category_scores(
    evaluation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get category scores for an evaluation"""
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    # Verify access
    recording = db.query(Recording).filter(
        Recording.id == evaluation.recording_id,
        Recording.company_id == current_user.company_id
    ).first()
    
    if not recording:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {
        "evaluation_id": evaluation.id,
        "category_scores": [
            {
                "id": score.id,
                "category_name": score.category_name,
                "score": score.score,
                "feedback": score.feedback
            }
            for score in evaluation.category_scores
        ]
    }


@router.get("/{evaluation_id}/violations")
async def get_policy_violations(
    evaluation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get compliance rule violations for an evaluation (from Phase 3 deterministic results)"""
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    # Verify access
    recording = db.query(Recording).filter(
        Recording.id == evaluation.recording_id,
        Recording.company_id == current_user.company_id
    ).first()
    
    if not recording:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get violations from deterministic_results (Phase 3)
    violations = []
    if evaluation.deterministic_results and isinstance(evaluation.deterministic_results, dict):
        rule_violations = evaluation.deterministic_results.get("rule_violations", [])
        violations = [
            {
                "rule_id": v.get("rule_id"),
                "rule_type": v.get("rule_type"),
                "description": v.get("description"),
                "severity": v.get("severity"),
                "stage_id": v.get("stage_id"),
                "step_id": v.get("step_id")
            }
            for v in rule_violations
        ]
    
    return {
        "evaluation_id": evaluation.id,
        "violations": violations
    }
