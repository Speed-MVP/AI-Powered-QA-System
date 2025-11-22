"""
Human Review API Routes
MVP Evaluation Improvements - Phase 2
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, desc
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models.human_review import HumanReview, ReviewStatus
from app.models.evaluation import Evaluation
from app.models.recording import Recording
from app.models.user import User
from app.models.rule_engine_results import RuleEngineResults
from app.middleware.auth import get_current_user
from app.schemas.human_review import HumanReviewCreate, HumanReviewResponse, HumanReviewQueueItem

router = APIRouter()


@router.get("/queue", response_model=List[HumanReviewQueueItem])
async def get_human_review_queue(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get queue of recordings requiring human review.
    Returns evaluations that need human review with full context.
    """
    # Get evaluations requiring human review
    evaluations = db.query(Evaluation).options(
        joinedload(Evaluation.recording),
        joinedload(Evaluation.category_scores),
        joinedload(Evaluation.human_review)
    ).filter(
        and_(
            Evaluation.requires_human_review == True,
            Evaluation.status == "completed"
        )
    ).order_by(
        desc(Evaluation.created_at)
    ).limit(limit).all()

    queue_items = []
    for evaluation in evaluations:
        # Get rule engine results
        rule_results = db.query(RuleEngineResults).filter(
            RuleEngineResults.evaluation_id == evaluation.id
        ).first()

        # Check if already has pending human review
        existing_review = db.query(HumanReview).filter(
            and_(
                HumanReview.evaluation_id == evaluation.id,
                HumanReview.status.in_([ReviewStatus.pending, ReviewStatus.in_progress])
            )
        ).first()

        if existing_review:
            continue  # Skip if already in queue

        queue_item = HumanReviewQueueItem(
            evaluation_id=evaluation.id,
            recording_id=evaluation.recording_id,
            recording_title=evaluation.recording.file_name if evaluation.recording else "Unknown",
            ai_overall_score=evaluation.overall_score,
            ai_category_scores={cs.category_name: cs.score for cs in evaluation.category_scores},
            ai_violations=evaluation.llm_analysis.get("violations", []) if evaluation.llm_analysis else [],
            rule_engine_results=rule_results.rules if rule_results else {},
            confidence_score=evaluation.confidence_score,
            transcript_preview=evaluation.recording.transcript.transcript_text[:500] + "..." if evaluation.recording and evaluation.recording.transcript else "",
            created_at=evaluation.created_at
        )
        queue_items.append(queue_item)

    return queue_items


@router.post("/{evaluation_id}", response_model=HumanReviewResponse)
async def submit_human_review(
    evaluation_id: str,
    review_data: HumanReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit human review for an evaluation.
    Updates evaluation status and saves human corrections.
    """
    # Get evaluation
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    # Check if evaluation requires human review
    if not evaluation.requires_human_review:
        raise HTTPException(status_code=400, detail="Evaluation does not require human review")

    # Check if human review already exists
    existing_review = db.query(HumanReview).filter(
        HumanReview.evaluation_id == evaluation_id
    ).first()

    if existing_review:
        raise HTTPException(status_code=400, detail="Human review already exists for this evaluation")

    # Create human review record
    human_review = HumanReview(
        recording_id=evaluation.recording_id,
        evaluation_id=evaluation_id,
        reviewer_user_id=current_user.id,
        human_overall_score=review_data.human_scores.get("Overall") or review_data.overall_score,
        human_category_scores=review_data.human_scores,
        human_violations=review_data.human_violations,
        reviewer_notes=review_data.reviewer_notes,
        ai_scores=evaluation.llm_analysis,  # Snapshot of AI evaluation
        delta=_compute_human_ai_delta(evaluation.llm_analysis, review_data),
        review_status=ReviewStatus.completed
    )

    db.add(human_review)

    # Update evaluation status
    evaluation.status = "reviewed"
    evaluation.requires_human_review = False

    # Optionally update evaluation scores with human corrections if requested
    if review_data.corrections:
        if "overall_score" in review_data.corrections:
            evaluation.overall_score = review_data.corrections["overall_score"]
        if "category_scores" in review_data.corrections:
            # Update category scores
            for cat_name, new_score in review_data.corrections["category_scores"].items():
                cat_score = next((cs for cs in evaluation.category_scores if cs.category_name == cat_name), None)
                if cat_score:
                    cat_score.score = new_score

    db.commit()
    db.refresh(human_review)

    return HumanReviewResponse.from_orm(human_review)


@router.get("/{evaluation_id}", response_model=HumanReviewResponse)
async def get_human_review(
    evaluation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get human review for an evaluation."""
    review = db.query(HumanReview).filter(HumanReview.evaluation_id == evaluation_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Human review not found")

    return HumanReviewResponse.from_orm(review)


@router.get("/", response_model=List[HumanReviewResponse])
async def list_human_reviews(
    status: Optional[ReviewStatus] = None,
    reviewer_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List human reviews with optional filtering."""
    query = db.query(HumanReview).options(
        joinedload(HumanReview.evaluation).joinedload(Evaluation.recording)
    )

    if status:
        query = query.filter(HumanReview.status == status)
    if reviewer_id:
        query = query.filter(HumanReview.reviewer_user_id == reviewer_id)

    reviews = query.order_by(desc(HumanReview.created_at)).limit(limit).all()
    return [HumanReviewResponse.from_orm(review) for review in reviews]


def _compute_human_ai_delta(ai_evaluation: dict, human_review: HumanReviewCreate) -> dict:
    """
    Compute the delta between AI evaluation and human review.
    Used for audit and override tracking only - NOT for training.
    """
    delta = {
        "overall_score_diff": None,
        "category_score_diffs": {},
        "violation_diffs": [],
        "computed_at": datetime.utcnow().isoformat()
    }

    if not ai_evaluation:
        return delta

    # Overall score difference
    ai_overall = ai_evaluation.get("overall_score")
    human_overall = human_review.human_scores.get("Overall") or human_review.overall_score
    if ai_overall is not None and human_overall is not None:
        delta["overall_score_diff"] = human_overall - ai_overall

    # Category score differences
    ai_categories = ai_evaluation.get("category_scores", {})
    human_categories = human_review.human_scores

    for cat_name in set(ai_categories.keys()) | set(human_categories.keys()):
        ai_score = ai_categories.get(cat_name)
        human_score = human_categories.get(cat_name)
        if ai_score is not None and human_score is not None:
            delta["category_score_diffs"][cat_name] = human_score - ai_score

    # Violation differences (simplified)
    ai_violations = ai_evaluation.get("violations", [])
    human_violations = human_review.human_violations or []

    delta["violation_diffs"] = {
        "ai_count": len(ai_violations),
        "human_count": len(human_violations),
        "difference": len(human_violations) - len(ai_violations)
    }

    return delta
