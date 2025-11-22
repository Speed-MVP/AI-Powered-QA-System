"""
Supervisor API Routes for QA Management
Phase 4: Scale & Optimization
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from app.database import SessionLocal
from app.models.evaluation import Evaluation, EvaluationStatus
from app.models.recording import Recording
from app.models.category_score import CategoryScore
# Legacy: PolicyViolation removed - violations are now stored in deterministic_results JSONB
from app.models.human_review import HumanReview, ReviewStatus
from app.services.gemini import GeminiService
from app.services.confidence import ConfidenceService
from app.tasks.process_recording import process_recording_task
from sqlalchemy import func
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/supervisor", tags=["supervisor"])


@router.get("/evaluations")
async def get_evaluations(
    status: Optional[str] = Query(None, description="Filter by evaluation status"),
    requires_review: Optional[bool] = Query(None, description="Filter by human review requirement"),
    confidence_min: Optional[float] = Query(None, description="Minimum confidence score"),
    confidence_max: Optional[float] = Query(None, description="Maximum confidence score"),
    date_from: Optional[datetime] = Query(None, description="Filter from date"),
    date_to: Optional[datetime] = Query(None, description="Filter to date"),
    limit: int = Query(50, description="Maximum results to return"),
    offset: int = Query(0, description="Pagination offset")
):
    """
    Get evaluations with advanced filtering for supervisor review.
    """
    db = SessionLocal()
    try:
        query = db.query(Evaluation).join(Recording)

        # Apply filters
        if status:
            query = query.filter(Evaluation.status == status)
        if requires_review is not None:
            query = query.filter(Evaluation.requires_human_review == requires_review)
        if confidence_min is not None:
            query = query.filter(Evaluation.confidence_score >= confidence_min)
        if confidence_max is not None:
            query = query.filter(Evaluation.confidence_score <= confidence_max)
        if date_from:
            query = query.filter(Recording.uploaded_at >= date_from)
        if date_to:
            query = query.filter(Recording.uploaded_at <= date_to)

        # Get total count
        total_count = query.count()

        # Apply pagination and get results
        evaluations = query.order_by(Recording.uploaded_at.desc()).offset(offset).limit(limit).all()

        # Format results
        results = []
        for eval in evaluations:
            recording = eval.recording
            results.append({
                "evaluation_id": eval.id,
                "recording_id": recording.id,
                "file_name": recording.file_name,
                "duration": recording.duration_seconds,
                "overall_score": eval.overall_score,
                "confidence_score": eval.confidence_score,
                "requires_human_review": eval.requires_human_review,
                "status": eval.status.value,
                "model_used": eval.llm_analysis.get("model_used", "unknown") if eval.llm_analysis else "unknown",
                "complexity_score": eval.llm_analysis.get("complexity_score", 0) if eval.llm_analysis else 0,
                "uploaded_at": recording.uploaded_at.isoformat(),
                "processed_at": eval.created_at.isoformat(),
                "has_human_review": eval.human_review is not None
            })

        return {
            "success": True,
            "data": results,
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_count
            }
        }
    finally:
        db.close()


@router.get("/evaluations/{evaluation_id}")
async def get_evaluation_details(evaluation_id: str):
    """
    Get detailed evaluation information including scores, violations, and analysis.
    """
    db = SessionLocal()
    try:
        evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
        if not evaluation:
            raise HTTPException(status_code=404, detail="Evaluation not found")

        recording = evaluation.recording

        # Get category scores
        category_scores = []
        for score in evaluation.category_scores:
            category_scores.append({
                "category": score.category_name,
                "score": score.score,
                "feedback": score.feedback
            })

        # Get violations
        violations = []
        for violation in evaluation.policy_violations:
            violations.append({
                "category": violation.criteria.category_name if violation.criteria else "Unknown",
                "type": violation.violation_type,
                "description": violation.description,
                "severity": violation.severity
            })

        # Get human review if exists
        human_review = None
        if evaluation.human_review:
            hr = evaluation.human_review
            human_review = {
                "reviewer_id": hr.reviewer_user_id,
                "human_overall_score": hr.human_overall_score,
                "human_category_scores": hr.human_category_scores,
                "ai_accuracy_rating": hr.ai_score_accuracy,
                "recommendation": hr.ai_recommendation,
                "time_spent_seconds": hr.time_spent_seconds,
                "reviewed_at": hr.created_at.isoformat()
            }

        return {
            "success": True,
            "data": {
                "evaluation_id": evaluation.id,
                "recording": {
                    "id": recording.id,
                    "file_name": recording.file_name,
                    "duration": recording.duration_seconds,
                    "uploaded_at": recording.uploaded_at.isoformat()
                },
                "ai_evaluation": {
                    "overall_score": evaluation.overall_score,
                    "confidence_score": evaluation.confidence_score,
                    "requires_human_review": evaluation.requires_human_review,
                    "resolution_detected": evaluation.resolution_detected,
                    "resolution_confidence": evaluation.resolution_confidence,
                    "model_used": evaluation.llm_analysis.get("model_used", "unknown") if evaluation.llm_analysis else "unknown",
                    "complexity_score": evaluation.llm_analysis.get("complexity_score", 0) if evaluation.llm_analysis else 0,
                    "category_scores": category_scores,
                    "violations": violations,
                    "customer_tone": evaluation.customer_tone
                },
                "human_review": human_review,
                "transcript": evaluation.recording.transcript.transcript_text if evaluation.recording.transcript else None,
                "status": evaluation.status.value,
                "created_at": evaluation.created_at.isoformat()
            }
        }
    finally:
        db.close()


@router.post("/evaluations/{evaluation_id}/override")
async def override_evaluation_score(
    evaluation_id: str,
    overall_score: int,
    category_scores: Dict[str, Dict[str, Any]],
    reason: str,
    reviewer_id: str
):
    """
    Supervisor override of AI evaluation scores.
    """
    if not (0 <= overall_score <= 100):
        raise HTTPException(status_code=400, detail="Overall score must be between 0 and 100")

    db = SessionLocal()
    try:
        evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
        if not evaluation:
            raise HTTPException(status_code=404, detail="Evaluation not found")

        # Update evaluation status
        evaluation.status = EvaluationStatus.reviewed

        # Create or update human review
        if evaluation.human_review:
            # Update existing review
            evaluation.human_review.human_overall_score = overall_score
            evaluation.human_review.human_category_scores = category_scores
            evaluation.human_review.ai_recommendation = reason
            evaluation.human_review.updated_at = datetime.utcnow()
        else:
            # Create new human review
            human_review = HumanReview(
                recording_id=evaluation.recording_id,
                evaluation_id=evaluation_id,
                reviewer_user_id=reviewer_id,
                human_overall_score=overall_score,
                human_category_scores=category_scores,
                ai_score_accuracy=5.0,  # Supervisor override = perfect accuracy
                ai_recommendation=reason,
                review_status=ReviewStatus.completed
            )
            db.add(human_review)

        # Update category scores if provided
        if category_scores:
            for category_name, score_data in category_scores.items():
                # Find existing category score
                cat_score = db.query(CategoryScore).filter(
                    CategoryScore.evaluation_id == evaluation_id,
                    CategoryScore.category_name == category_name
                ).first()

                if cat_score:
                    cat_score.score = score_data.get("score", cat_score.score)
                    cat_score.feedback = score_data.get("feedback", cat_score.feedback)

        db.commit()

        logger.info(f"Supervisor override applied to evaluation {evaluation_id}")

        return {
            "success": True,
            "message": "Evaluation override applied successfully",
            "evaluation_id": evaluation_id
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error overriding evaluation: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/evaluations/{evaluation_id}/re-score")
async def re_score_evaluation(evaluation_id: str, background_tasks: BackgroundTasks):
    """
    Re-run evaluation for a recording (useful for testing model improvements).
    """
    db = SessionLocal()
    try:
        evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
        if not evaluation:
            raise HTTPException(status_code=404, detail="Evaluation not found")

        recording = evaluation.recording
        if not recording:
            raise HTTPException(status_code=404, detail="Recording not found")

        # Mark evaluation as pending re-processing
        evaluation.status = EvaluationStatus.pending

        # Trigger background re-processing
        background_tasks.add_task(process_recording_task, recording.id)

        logger.info(f"Re-scoring triggered for evaluation {evaluation_id}")

        return {
            "success": True,
            "message": "Re-scoring initiated in background",
            "evaluation_id": evaluation_id,
            "recording_id": recording.id
        }
    finally:
        db.close()


@router.get("/analytics/overview")
async def get_qa_analytics(days: int = 30):
    """
    Get QA performance analytics for supervisor dashboard.
    """
    db = SessionLocal()
    try:
        date_from = datetime.utcnow() - timedelta(days=days)

        # Basic metrics
        total_evaluations = db.query(Evaluation).join(Recording).filter(
            Recording.uploaded_at >= date_from
        ).count()

        avg_score = db.query(Evaluation).join(Recording).filter(
            Recording.uploaded_at >= date_from
        ).avg_score = db.session.query(func.avg(Evaluation.overall_score)).join(Recording).filter(
            Recording.uploaded_at >= date_from
        ).scalar() or 0

        avg_confidence = db.query(Evaluation).join(Recording).filter(
            Recording.uploaded_at >= date_from,
            Evaluation.confidence_score.isnot(None)
        ).avg_confidence = db.session.query(func.avg(Evaluation.confidence_score)).join(Recording).filter(
            Recording.uploaded_at >= date_from,
            Evaluation.confidence_score.isnot(None)
        ).scalar() or 0

        human_review_rate = db.query(Evaluation).join(Recording).filter(
            Recording.uploaded_at >= date_from,
            Evaluation.requires_human_review == True
        ).count() / max(total_evaluations, 1)

        # Model usage statistics
        flash_count = db.query(Evaluation).join(Recording).filter(
            Recording.uploaded_at >= date_from,
            Evaluation.llm_analysis.contains({"model_used": "gemini-1.5-flash"})
        ).count()

        pro_count = db.query(Evaluation).join(Recording).filter(
            Recording.uploaded_at >= date_from,
            Evaluation.llm_analysis.contains({"model_used": "gemini-1.5-pro"})
        ).count()

        # Top violations
        violation_stats = db.query(
            PolicyViolation.violation_type,
            PolicyViolation.severity,
            db.func.count(PolicyViolation.id).label('count')
        ).join(Evaluation).join(Recording).filter(
            Recording.uploaded_at >= date_from
        ).group_by(PolicyViolation.violation_type, PolicyViolation.severity).all()

        top_violations = [
            {
                "violation_type": v.violation_type,
                "severity": v.severity,
                "count": v.count
            }
            for v in sorted(violation_stats, key=lambda x: x.count, reverse=True)[:10]
        ]

        return {
            "success": True,
            "data": {
                "period_days": days,
                "total_evaluations": total_evaluations,
                "average_score": round(float(avg_score), 1),
                "average_confidence": round(float(avg_confidence), 3),
                "human_review_rate": round(human_review_rate, 3),
                "model_usage": {
                    "flash_model": flash_count,
                    "pro_model": pro_count,
                    "cost_savings_estimate": round(flash_count * 0.4, 1)  # Rough estimate
                },
                "top_violations": top_violations
            }
        }
    finally:
        db.close()


@router.get("/analytics/trends")
async def get_qa_trends(days: int = 30):
    """
    Get QA performance trends over time.
    """
    db = SessionLocal()
    try:
        date_from = datetime.utcnow() - timedelta(days=days)

        # Daily metrics
        daily_stats = []
        for i in range(days):
            day_start = date_from + timedelta(days=i)
            day_end = day_start + timedelta(days=1)

            day_evaluations = db.query(Evaluation).join(Recording).filter(
                Recording.uploaded_at >= day_start,
                Recording.uploaded_at < day_end
            ).all()

            if day_evaluations:
                avg_score = sum(e.overall_score for e in day_evaluations) / len(day_evaluations)
                avg_confidence = sum(e.confidence_score or 0 for e in day_evaluations) / len(day_evaluations)
                human_reviews = sum(1 for e in day_evaluations if e.requires_human_review)
            else:
                avg_score = 0
                avg_confidence = 0
                human_reviews = 0

            daily_stats.append({
                "date": day_start.strftime("%Y-%m-%d"),
                "evaluations": len(day_evaluations),
                "avg_score": round(avg_score, 1),
                "avg_confidence": round(avg_confidence, 3),
                "human_reviews": human_reviews
            })

        return {
            "success": True,
            "data": {
                "period_days": days,
                "daily_trends": daily_stats
            }
        }
    finally:
        db.close()
