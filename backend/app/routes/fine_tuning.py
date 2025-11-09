"""
Fine-Tuning API Routes
Phase 3: Fine-Tuning & Self-Learning
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.services.dataset_curation import DatasetCurationService
from app.services.fine_tuning import FineTuningService
from app.services.continuous_learning import ContinuousLearningService
from typing import Dict, Any
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
