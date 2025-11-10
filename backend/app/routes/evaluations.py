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
        "policy_template_id": evaluation.policy_template_id,
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
        "policy_violations": [
            {
                "id": violation.id,
                "violation_type": violation.violation_type,
                "description": violation.description,
                "severity": violation.severity.value,
                "criteria_id": violation.criteria_id
            }
            for violation in evaluation.policy_violations
        ]
    }
    
    return evaluation_dict


@router.get("/{recording_id}/with-template")
async def get_evaluation_with_template(
    recording_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get evaluation results with full template details for human review"""
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

    # Get policy template with criteria and rubric levels
    from sqlalchemy.orm import joinedload
    from app.models.policy_template import PolicyTemplate

    template = db.query(PolicyTemplate).options(
        joinedload(PolicyTemplate.criteria).joinedload('rubric_levels')
    ).filter(
        PolicyTemplate.id == evaluation.policy_template_id,
        PolicyTemplate.company_id == current_user.company_id
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="Policy template not found")

    # Convert customer_tone JSONB to dict if it exists
    evaluation_dict = {
        "id": evaluation.id,
        "recording_id": evaluation.recording_id,
        "policy_template_id": evaluation.policy_template_id,
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
        "policy_violations": [
            {
                "id": violation.id,
                "violation_type": violation.violation_type,
                "description": violation.description,
                "severity": violation.severity.value,
                "criteria_id": violation.criteria_id
            }
            for violation in evaluation.policy_violations
        ],
        "template": {
            "id": template.id,
            "template_name": template.template_name,
            "description": template.description,
            "criteria": [
                {
                    "id": criterion.id,
                    "category_name": criterion.category_name,
                    "weight": criterion.weight,
                    "passing_score": criterion.passing_score,
                    "evaluation_prompt": criterion.evaluation_prompt,
                    "rubric_levels": [
                        {
                            "id": level.id,
                            "level_name": level.level_name,
                            "level_order": level.level_order,
                            "min_score": level.min_score,
                            "max_score": level.max_score,
                            "description": level.description,
                            "examples": level.examples
                        }
                        for level in sorted(criterion.rubric_levels, key=lambda x: x.level_order)
                    ]
                }
                for criterion in template.criteria
            ]
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
    """Get policy violations for an evaluation"""
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
        "violations": [
            {
                "id": violation.id,
                "violation_type": violation.violation_type,
                "description": violation.description,
                "severity": violation.severity.value,
                "criteria_id": violation.criteria_id
            }
            for violation in evaluation.policy_violations
        ]
    }

