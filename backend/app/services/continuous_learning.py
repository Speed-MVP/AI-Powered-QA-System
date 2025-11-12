"""
Continuous Learning Service for Model Improvement
Phase 3: Fine-Tuning & Self-Learning
"""

from app.database import SessionLocal
from app.models.human_review import HumanReview, FineTuningDataset, ModelPerformance
from app.services.dataset_curation import DatasetCurationService
from app.services.fine_tuning import FineTuningService
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timedelta
import schedule
import threading
import time

logger = logging.getLogger(__name__)


class ContinuousLearningService:
    """
    Service for continuous model improvement through regular retraining.
    Phase 3: Weekly retrain fine-tuning dataset with newly reviewed calls.
    """

    def __init__(self):
        self.dataset_service = DatasetCurationService()
        self.fine_tuning_service = FineTuningService()
        self.retraining_interval_days = 7  # Weekly retraining
        self.min_new_reviews_for_retraining = 50  # Minimum new reviews to trigger retraining

    def start_continuous_learning(self) -> Dict[str, Any]:
        """
        Start the continuous learning process.
        This would run as a background service in production.
        """
        try:
            # Schedule weekly retraining
            schedule.every(self.retraining_interval_days).days.do(self._perform_weekly_retraining)

            # Start background thread for continuous learning
            learning_thread = threading.Thread(target=self._run_continuous_learning, daemon=True)
            learning_thread.start()

            logger.info(f"Started continuous learning with {self.retraining_interval_days}-day intervals")

            return {
                "success": True,
                "status": "running",
                "retraining_interval_days": self.retraining_interval_days,
                "min_new_reviews_threshold": self.min_new_reviews_for_retraining
            }

        except Exception as e:
            logger.error(f"Failed to start continuous learning: {e}")
            return {"success": False, "error": str(e)}

    def _run_continuous_learning(self):
        """Background thread for continuous learning."""
        logger.info("Continuous learning thread started")

        while True:
            try:
                schedule.run_pending()
                time.sleep(3600)  # Check every hour
            except Exception as e:
                logger.error(f"Error in continuous learning loop: {e}")
                time.sleep(300)  # Wait 5 minutes before retrying

    def _perform_weekly_retraining(self) -> Dict[str, Any]:
        """
        Perform weekly model retraining if sufficient new data is available.
        """
        try:
            logger.info("Starting weekly retraining check")

            # Check if we have enough new reviews for retraining
            new_reviews_count = self._count_new_reviews_since_last_training()

            if new_reviews_count < self.min_new_reviews_for_retraining:
                logger.info(f"Insufficient new reviews: {new_reviews_count}/{self.min_new_reviews_for_retraining}. Skipping retraining.")
                return {
                    "success": True,
                    "action": "skipped",
                    "reason": "insufficient_data",
                    "new_reviews": new_reviews_count
                }

            # Create new dataset version
            dataset_result = self._create_updated_dataset()

            if not dataset_result["success"]:
                return dataset_result

            # Start fine-tuning job
            fine_tuning_result = self.fine_tuning_service.start_fine_tuning_job(
                dataset_result["dataset_id"]
            )

            if not fine_tuning_result["success"]:
                return fine_tuning_result

            # Update active dataset
            self._update_active_dataset(dataset_result["dataset_id"])

            logger.info(f"Weekly retraining completed successfully. New dataset: {dataset_result['dataset_id']}")

            return {
                "success": True,
                "action": "retrained",
                "dataset_id": dataset_result["dataset_id"],
                "job_id": fine_tuning_result["job_id"],
                "new_reviews_used": new_reviews_count
            }

        except Exception as e:
            logger.error(f"Error during weekly retraining: {e}")
            return {"success": False, "error": str(e)}

    def _count_new_reviews_since_last_training(self) -> int:
        """Count new reviews since the last training dataset was created."""
        db = SessionLocal()
        try:
            # Find the most recent training dataset
            latest_dataset = db.query(FineTuningDataset).filter(
                FineTuningDataset.fine_tuning_status == "completed"
            ).order_by(FineTuningDataset.created_at.desc()).first()

            if not latest_dataset:
                # No previous training, count all eligible reviews
                return db.query(HumanReview).filter(
                    HumanReview.review_status == 'completed',
                    HumanReview.included_in_training == False
                ).count()

            # Count reviews created after the latest dataset
            return db.query(HumanReview).filter(
                HumanReview.review_status == 'completed',
                HumanReview.included_in_training == False,
                HumanReview.created_at > latest_dataset.created_at
            ).count()

        finally:
            db.close()

    def _create_updated_dataset(self) -> Dict[str, Any]:
        """Create a new dataset version with recent reviews."""
        # Get current date for versioning
        today = datetime.utcnow().strftime("%Y%m%d")
        version = f"2.0.{today}"

        dataset_name = f"QA_FineTuning_{version}"
        description = f"Continuous learning update - {datetime.utcnow().strftime('%Y-%m-%d')}"

        # Create dataset using curation service
        return self.dataset_service.create_fine_tuning_dataset(
            name=dataset_name,
            description=description,
            min_reviews=self.min_new_reviews_for_retraining
        )

    def _update_active_dataset(self, new_dataset_id: str):
        """Update which dataset is currently active."""
        db = SessionLocal()
        try:
            # Deactivate current active dataset
            db.query(FineTuningDataset).filter(
                FineTuningDataset.is_active == True
            ).update({"is_active": False})

            # Activate new dataset
            new_dataset = db.query(FineTuningDataset).filter(
                FineTuningDataset.id == new_dataset_id
            ).first()

            if new_dataset:
                new_dataset.is_active = True
                db.commit()
                logger.info(f"Activated new dataset: {new_dataset_id}")

        finally:
            db.close()

    def get_learning_status(self) -> Dict[str, Any]:
        """Get current status of continuous learning system."""
        db = SessionLocal()
        try:
            # Get latest performance metrics
            latest_performance = db.query(ModelPerformance).order_by(
                ModelPerformance.created_at.desc()
            ).first()

            # Get active dataset
            active_dataset = db.query(FineTuningDataset).filter(
                FineTuningDataset.is_active == True
            ).first()

            # Get dataset statistics
            stats = self.dataset_service.get_dataset_statistics()

            # Calculate next retraining date
            if active_dataset:
                next_retraining = active_dataset.created_at + timedelta(days=self.retraining_interval_days)
                days_until_retraining = (next_retraining - datetime.utcnow()).days
            else:
                days_until_retraining = 0

            return {
                "continuous_learning_active": True,
                "retraining_interval_days": self.retraining_interval_days,
                "min_reviews_threshold": self.min_new_reviews_for_retraining,
                "days_until_next_retraining": max(0, days_until_retraining),
                "active_dataset": {
                    "id": active_dataset.id if active_dataset else None,
                    "name": active_dataset.name if active_dataset else None,
                    "version": active_dataset.version if active_dataset else None,
                    "created_at": active_dataset.created_at.isoformat() if active_dataset else None
                } if active_dataset else None,
                "latest_performance": {
                    "accuracy": float(latest_performance.accuracy_score) if latest_performance else None,
                    "human_agreement": float(latest_performance.human_agreement_rate) if latest_performance else None,
                    "human_review_rate": float(latest_performance.human_review_rate) if latest_performance else None,
                    "evaluated_at": latest_performance.created_at.isoformat() if latest_performance else None
                } if latest_performance else None,
                "dataset_statistics": stats
            }

        finally:
            db.close()

    def trigger_manual_retraining(self, force: bool = False) -> Dict[str, Any]:
        """
        Manually trigger retraining (for testing or urgent updates).
        """
        if force:
            logger.info("Manual retraining triggered (forced)")
            return self._perform_weekly_retraining()
        else:
            new_reviews = self._count_new_reviews_since_last_training()
            if new_reviews >= self.min_new_reviews_for_retraining:
                logger.info(f"Manual retraining triggered ({new_reviews} new reviews)")
                return self._perform_weekly_retraining()
            else:
                return {
                    "success": False,
                    "error": f"Insufficient new reviews: {new_reviews}/{self.min_new_reviews_for_retraining}"
                }





