"""
Fine-Tuning API Routes
Phase 3: Fine-Tuning & Self-Learning
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.dataset_curation import DatasetCurationService
from app.services.fine_tuning import FineTuningService
from app.services.continuous_learning import ContinuousLearningService
from app.services.storage import StorageService
from app.models.human_review import HumanReview, ReviewStatus
from app.models.evaluation import Evaluation
from app.models.transcript import Transcript
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.human_review import HumanReviewSubmit
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/fine-tuning", tags=["fine-tuning"])


@router.get("/dataset/statistics")
async def get_dataset_statistics():
    """
    Get current statistics about human-reviewed data available for fine-tuning.
    """
    try:
        service = DatasetCurationService()
        stats = service.get_dataset_statistics()
        return {"success": True, "data": stats}
    except Exception as e:
        logger.error(f"Error getting dataset statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dataset/create")
async def create_fine_tuning_dataset(
    name: str,
    description: str = "",
    min_reviews: int = 100,
    quality_threshold: float = 3.0
):
    """
    Create a new fine-tuning dataset from high-quality human reviews.
    """
    try:
        service = DatasetCurationService()
        result = service.create_fine_tuning_dataset(
            name=name,
            description=description,
            min_reviews=min_reviews,
            quality_threshold=quality_threshold
        )

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])

        return {"success": True, "data": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating fine-tuning dataset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/train/start")
async def start_fine_tuning_job(dataset_id: str):
    """
    Start a fine-tuning job for the specified dataset.
    """
    try:
        service = FineTuningService()
        result = service.start_fine_tuning_job(dataset_id)

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])

        return {"success": True, "data": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting fine-tuning job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/train/status/{job_id}")
async def check_fine_tuning_status(job_id: str):
    """
    Check the status of a fine-tuning job.
    """
    try:
        service = FineTuningService()
        result = service.check_fine_tuning_status(job_id)

        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["error"])

        return {"success": True, "data": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking fine-tuning status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluate/performance")
async def evaluate_model_performance(
    model_version: str = "gemini-1.5-pro",
    evaluation_period_days: int = 30
):
    """
    Evaluate current model performance against human reviews.
    """
    try:
        service = FineTuningService()
        result = service.evaluate_model_performance(
            model_version=model_version,
            evaluation_period_days=evaluation_period_days
        )

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])

        return {"success": True, "data": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error evaluating model performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/continuous-learning/status")
async def get_continuous_learning_status():
    """
    Get the current status of the continuous learning system.
    """
    try:
        service = ContinuousLearningService()
        status = service.get_learning_status()
        return {"success": True, "data": status}
    except Exception as e:
        logger.error(f"Error getting continuous learning status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/continuous-learning/start")
async def start_continuous_learning():
    """
    Start the continuous learning system.
    """
    try:
        service = ContinuousLearningService()
        result = service.start_continuous_learning()

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])

        return {"success": True, "data": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting continuous learning: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/continuous-learning/retrain")
async def trigger_manual_retraining(force: bool = False):
    """
    Manually trigger model retraining.
    """
    try:
        service = ContinuousLearningService()
        result = service.trigger_manual_retraining(force=force)
        return {"success": result["success"], "data": result}
    except Exception as e:
        logger.error(f"Error triggering manual retraining: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Human Review Endpoints
@router.get("/human-reviews/pending", response_model=List[Dict[str, Any]])
async def get_pending_reviews(
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get pending human reviews for the current user.
    """
    try:
        logger.info(f"Getting pending reviews for user {current_user.id}")

        # Get pending reviews with all related data using eager loading
        from sqlalchemy.orm import joinedload
        from app.models.recording import Recording
        
        reviews = db.query(HumanReview).options(
            joinedload(HumanReview.evaluation).joinedload(Evaluation.recording)
        ).filter(
            HumanReview.review_status == ReviewStatus.pending
        ).offset(skip).limit(limit).all()

        logger.info(f"Found {len(reviews)} pending reviews")

        if not reviews:
            return []

        # Batch load all transcripts in one query
        evaluation_ids = [r.evaluation_id for r in reviews if r.evaluation_id]
        recording_ids = [r.evaluation.recording_id for r in reviews if r.evaluation and r.evaluation.recording_id]
        
        transcripts = db.query(Transcript).filter(
            Transcript.recording_id.in_(recording_ids)
        ).all()
        
        # Create a mapping for quick lookup
        transcript_map = {t.recording_id: t for t in transcripts}

        # Batch get audio URLs (if needed)
        from app.services.storage import StorageService
        storage_service = StorageService()
        
        result = []
        for review in reviews:
            evaluation = review.evaluation
            if not evaluation:
                logger.warning(f"Review {review.id} has no associated evaluation")
                continue

            recording_id = evaluation.recording_id
            transcript = transcript_map.get(recording_id)

            if not transcript:
                logger.warning(f"No transcript found for recording {recording_id}")
                continue

            # Get audio download URL (only if recording exists)
            audio_url = None
            if evaluation.recording:
                try:
                    blob_name = f"{evaluation.recording.company_id}/{evaluation.recording.file_name}"
                    audio_url = storage_service.get_signed_download_url(blob_name, expiration_minutes=60)
                except Exception as e:
                    logger.warning(f"Could not get audio URL for recording {evaluation.recording.id}: {e}")

            result.append({
                "review_id": review.id,
                "evaluation_id": evaluation.id,
                "transcript_text": transcript.transcript_text if transcript else "",
                "diarized_segments": transcript.diarized_segments if transcript else [],
                "audio_url": audio_url,
                "ai_overall_score": evaluation.overall_score,
                "ai_category_scores": evaluation.llm_analysis.get("category_scores", {}) if evaluation.llm_analysis else {},
                "ai_violations": evaluation.llm_analysis.get("violations", []) if evaluation.llm_analysis else [],
                "created_at": review.created_at.isoformat()
            })

        logger.info(f"Returning {len(result)} formatted reviews")
        return result
    except Exception as e:
        logger.error(f"Error getting pending reviews: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/human-reviews/test-create")
async def create_test_human_review(
    evaluation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a test human review for testing purposes.
    """
    try:
        # Check if evaluation exists
        evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
        if not evaluation:
            raise HTTPException(status_code=404, detail="Evaluation not found")

        # Check if review already exists
        existing_review = db.query(HumanReview).filter(HumanReview.evaluation_id == evaluation_id).first()
        if existing_review:
            raise HTTPException(status_code=400, detail="Review already exists for this evaluation")

        # Create test review
        review = HumanReview(
            evaluation_id=evaluation_id,
            reviewer_user_id=None,  # Will be assigned when picked up
            review_status=ReviewStatus.pending,
            ai_score_accuracy=None,
            human_overall_score=None,
            human_category_scores=None
        )
        db.add(review)
        db.commit()
        db.refresh(review)

        return {"message": "Test human review created", "review_id": review.id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating test human review: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/human-reviews/{review_id}/submit")
async def submit_human_review(
    review_id: str,
    review_data: HumanReviewSubmit,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit a completed human review.
    """
    try:
        logger.info(f"Submitting human review {review_id} by user {current_user.id}")
        
        review = db.query(HumanReview).filter(HumanReview.id == review_id).first()
        if not review:
            logger.warning(f"Review {review_id} not found")
            raise HTTPException(status_code=404, detail=f"Review {review_id} not found")
        
        if review.review_status != ReviewStatus.pending:
            logger.warning(f"Review {review_id} is not pending (status: {review.review_status})")
            raise HTTPException(
                status_code=400, 
                detail=f"Review is not pending. Current status: {review.review_status}"
            )

        # Update review
        review.human_overall_score = review_data.human_overall_score
        review.human_category_scores = review_data.human_category_scores
        review.ai_score_accuracy = review_data.ai_score_accuracy
        review.reviewer_user_id = current_user.id
        review.review_status = ReviewStatus.completed

        db.commit()

        # Add to active dataset for learning
        curation_service = DatasetCurationService()
        curation_service.add_review_to_active_dataset(review_id, db)

        logger.info(f"Human review {review_id} submitted by {current_user.id}")

        return {"message": "Human review submitted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting human review: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


