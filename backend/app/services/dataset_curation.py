"""
Dataset Curation Service for Fine-Tuning
Phase 3: Fine-Tuning & Self-Learning
"""

from app.database import SessionLocal
from app.models.human_review import HumanReview, FineTuningDataset, FineTuningSample, ModelPerformance, ReviewStatus
from app.models.evaluation import Evaluation
from app.models.transcript import Transcript
from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime, timedelta
import numpy as np
from sklearn.model_selection import train_test_split

logger = logging.getLogger(__name__)


class DatasetCurationService:
    """
    Service for curating fine-tuning datasets from human-reviewed evaluations.
    Phase 3: Collect at least 1,000 human-reviewed calls with transcripts, audio metadata,
    and final human QA scores per category.
    """

    def __init__(self):
        self.min_samples_for_training = 100  # Minimum samples for meaningful fine-tuning
        self.target_samples = 1000  # Target: 1000+ samples

    def get_dataset_statistics(self) -> Dict[str, Any]:
        """
        Get current statistics about available human-reviewed data for fine-tuning.
        """
        db = SessionLocal()
        try:
            # Count total human reviews
            total_reviews = db.query(HumanReview).count()

            # Count reviews by status
            status_counts = {}
            for status in ['pending', 'in_review', 'completed', 'disputed']:
                count = db.query(HumanReview).filter(HumanReview.review_status == status).count()
                status_counts[status] = count

            # Count reviews included in training
            training_reviews = db.query(HumanReview).filter(HumanReview.included_in_training == True).count()

            # Get active datasets
            active_datasets = db.query(FineTuningDataset).filter(FineTuningDataset.is_active == True).all()

            # Calculate quality metrics
            completed_reviews = db.query(HumanReview).filter(HumanReview.review_status == 'completed').all()

            if completed_reviews:
                avg_accuracy_rating = np.mean([r.ai_score_accuracy for r in completed_reviews])
                avg_difficulty = np.mean([r.difficulty_rating for r in completed_reviews if r.difficulty_rating])
            else:
                avg_accuracy_rating = 0.0
                avg_difficulty = 0.0

            return {
                "total_human_reviews": total_reviews,
                "reviews_by_status": status_counts,
                "training_eligible_reviews": training_reviews,
                "active_datasets": len(active_datasets),
                "average_ai_accuracy_rating": round(float(avg_accuracy_rating), 2) if avg_accuracy_rating else None,
                "average_difficulty_rating": round(float(avg_difficulty), 2) if avg_difficulty else None,
                "training_readiness": self._assess_training_readiness(total_reviews, training_reviews),
                "data_quality_score": self._calculate_data_quality_score(completed_reviews)
            }

        finally:
            db.close()

    def create_fine_tuning_dataset(
        self,
        name: str,
        description: str = "",
        min_reviews: int = 100,
        quality_threshold: float = 3.0
    ) -> Dict[str, Any]:
        """
        Create a new fine-tuning dataset from high-quality human-reviewed evaluations.
        """
        db = SessionLocal()
        try:
            # Get eligible human reviews
            eligible_reviews = db.query(HumanReview).filter(
                HumanReview.review_status == 'completed',
                HumanReview.ai_score_accuracy >= quality_threshold,
                HumanReview.included_in_training == False
            ).all()

            if len(eligible_reviews) < min_reviews:
                return {
                    "success": False,
                    "error": f"Insufficient high-quality reviews. Found {len(eligible_reviews)}, need {min_reviews}",
                    "eligible_reviews": len(eligible_reviews)
                }

            # Create dataset
            dataset = FineTuningDataset(
                name=name,
                description=description,
                model_version="gemini-1.5-pro",
                version="1.0.0",
                total_samples=len(eligible_reviews)
            )
            db.add(dataset)
            db.flush()

            # Create training samples
            samples_created = 0
            for review in eligible_reviews:
                evaluation = db.query(Evaluation).filter(Evaluation.id == review.evaluation_id).first()
                if not evaluation:
                    continue

                transcript = db.query(Transcript).filter(Transcript.recording_id == evaluation.recording_id).first()
                if not transcript:
                    continue

                # Create sample
                sample = FineTuningSample(
                    dataset_id=dataset.id,
                    transcript_text=transcript.transcript_text,
                    diarized_segments=transcript.diarized_segments,
                    sentiment_analysis=transcript.sentiment_analysis,
                    voice_baselines=getattr(transcript, 'voice_baselines', None),
                    call_metadata=self._extract_call_metadata(evaluation, transcript),
                    policy_template_id=evaluation.policy_template_id,
                    expected_category_scores=review.human_category_scores,
                    expected_violations=self._extract_violations_from_evaluation(evaluation),
                    expected_overall_score=review.human_overall_score,
                    source_evaluation_id=evaluation.id,
                    quality_score=review.ai_score_accuracy,
                    difficulty_level=self._categorize_difficulty(review.difficulty_rating),
                    split="train",  # Will be reassigned during train/validation/test split
                    used_in_training=False
                )
                db.add(sample)
                samples_created += 1

                # Mark review as included in training
                review.included_in_training = True
                review.training_split = "train"  # Temporary, will be updated

            # Split into train/validation/test sets
            self._create_train_val_test_split(dataset.id, db)

            # Update dataset statistics
            dataset.training_samples = db.query(FineTuningSample).filter(
                FineTuningSample.dataset_id == dataset.id,
                FineTuningSample.split == "train"
            ).count()

            dataset.validation_samples = db.query(FineTuningSample).filter(
                FineTuningSample.dataset_id == dataset.id,
                FineTuningSample.split == "validation"
            ).count()

            dataset.test_samples = db.query(FineTuningSample).filter(
                FineTuningSample.dataset_id == dataset.id,
                FineTuningSample.split == "test"
            ).count()

            db.commit()

            logger.info(f"Created fine-tuning dataset '{name}' with {samples_created} samples")

            return {
                "success": True,
                "dataset_id": dataset.id,
                "samples_created": samples_created,
                "train_samples": dataset.training_samples,
                "val_samples": dataset.validation_samples,
                "test_samples": dataset.test_samples
            }

        except Exception as e:
            db.rollback()
            logger.error(f"Error creating fine-tuning dataset: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            db.close()

    def _create_train_val_test_split(self, dataset_id: str, db) -> None:
        """
        Split dataset samples into train/validation/test sets (80/10/10).
        """
        samples = db.query(FineTuningSample).filter(FineTuningSample.dataset_id == dataset_id).all()

        if len(samples) < 10:
            # For small datasets, put everything in train
            for sample in samples:
                sample.split = "train"
            return

        # Stratify by quality score to ensure balanced splits
        quality_scores = [sample.quality_score or 3.0 for sample in samples]

        # Create stratified split
        try:
            train_val, test = train_test_split(
                samples, test_size=0.1, stratify=quality_scores, random_state=42
            )
            train, val = train_test_split(
                train_val, test_size=0.111, stratify=[s.quality_score or 3.0 for s in train_val], random_state=42
            )

            # Update splits in database
            for sample in train:
                sample.split = "train"
            for sample in val:
                sample.split = "validation"
            for sample in test:
                sample.split = "test"

        except ValueError:
            # Fallback to random split if stratification fails
            logger.warning("Stratification failed, using random split")
            train_val, test = train_test_split(samples, test_size=0.1, random_state=42)
            train, val = train_test_split(train_val, test_size=0.111, random_state=42)

            for sample in train:
                sample.split = "train"
            for sample in val:
                sample.split = "validation"
            for sample in test:
                sample.split = "test"

    def _extract_call_metadata(self, evaluation: Evaluation, transcript: Transcript) -> Dict[str, Any]:
        """Extract call metadata for fine-tuning context."""
        return {
            "recording_id": evaluation.recording_id,
            "company_id": getattr(evaluation.recording, 'company_id', None) if evaluation.recording else None,
            "duration_seconds": getattr(evaluation.recording, 'duration_seconds', None) if evaluation.recording else None,
            "policy_template": evaluation.policy_template_id,
            "evaluated_at": evaluation.created_at.isoformat() if evaluation.created_at else None,
            "transcript_confidence": float(transcript.transcription_confidence) if transcript.transcription_confidence else None,
            "speaker_count": len(set([seg.get("speaker", "unknown") for seg in (transcript.diarized_segments or [])]))
        }

    def _extract_violations_from_evaluation(self, evaluation: Evaluation) -> List[Dict[str, Any]]:
        """Extract violations from evaluation for training labels."""
        violations = []
        for violation in evaluation.policy_violations:
            violations.append({
                "category_name": violation.criteria.category_name if violation.criteria else "Unknown",
                "type": violation.violation_type,
                "description": violation.description,
                "severity": violation.severity
            })
        return violations

    def _categorize_difficulty(self, difficulty_rating: Optional[float]) -> str:
        """Categorize difficulty rating into levels."""
        if not difficulty_rating:
            return "medium"

        if difficulty_rating >= 4.0:
            return "hard"
        elif difficulty_rating >= 3.0:
            return "medium"
        else:
            return "easy"

    def _assess_training_readiness(self, total_reviews: int, training_reviews: int) -> Dict[str, Any]:
        """Assess if we have enough data for training."""
        readiness_score = min(training_reviews / self.target_samples, 1.0)

        if training_reviews >= self.target_samples:
            status = "ready"
            message = f"Excellent! {training_reviews} training-ready reviews available (target: {self.target_samples})"
        elif training_reviews >= self.min_samples_for_training:
            status = "minimum_ready"
            message = f"Sufficient for initial training: {training_reviews} reviews (minimum: {self.min_samples_for_training})"
        else:
            status = "insufficient"
            message = f"Need more reviews: {training_reviews}/{self.min_samples_for_training} minimum required"

        return {
            "status": status,
            "readiness_score": round(readiness_score, 2),
            "message": message,
            "current_reviews": training_reviews,
            "target_reviews": self.target_samples,
            "minimum_reviews": self.min_samples_for_training
        }

    def _calculate_data_quality_score(self, completed_reviews: List[HumanReview]) -> float:
        """Calculate overall data quality score."""
        if not completed_reviews:
            return 0.0

        # Factors: AI accuracy rating, reviewer consistency, difficulty balance
        avg_accuracy = np.mean([r.ai_score_accuracy for r in completed_reviews])

        # Check difficulty distribution (prefer balanced)
        difficulties = [r.difficulty_rating for r in completed_reviews if r.difficulty_rating]
        if difficulties:
            difficulty_std = np.std(difficulties)
            difficulty_balance = 1.0 / (1.0 + difficulty_std)  # Lower std = better balance
        else:
            difficulty_balance = 0.5

        # Combine factors
        quality_score = (avg_accuracy * 0.7 + difficulty_balance * 0.3)

        return round(float(quality_score), 2)

    def add_review_to_active_dataset(self, review_id: str, db):
        """Add a completed human review to the active fine-tuning dataset for real-time learning."""
        try:
            review = db.query(HumanReview).filter(HumanReview.id == review_id).first()
            if not review or review.review_status != ReviewStatus.completed:
                logger.warning(f"Review {review_id} not found or not completed")
                return

            # Get evaluation and transcript
            evaluation = db.query(Evaluation).filter(Evaluation.id == review.evaluation_id).first()
            transcript = db.query(Transcript).filter(Transcript.recording_id == evaluation.recording_id).first()
            if not evaluation or not transcript:
                logger.warning(f"Evaluation or transcript not found for review {review_id}")
                return

            # Get or create active dataset
            active_dataset = db.query(FineTuningDataset).filter(FineTuningDataset.is_active == True).first()
            if not active_dataset:
                # Create active learning dataset
                active_dataset = FineTuningDataset(
                    name="Active_Learning_Dataset",
                    description="Real-time learning from human reviews",
                    model_version="gemini-1.5-pro",
                    is_active=True
                )
                db.add(active_dataset)
                db.flush()
                logger.info(f"Created new active dataset {active_dataset.id}")

            # Check if sample already exists
            existing_sample = db.query(FineTuningSample).filter(
                FineTuningSample.source_evaluation_id == evaluation.id
            ).first()
            if existing_sample:
                logger.info(f"Sample already exists for evaluation {evaluation.id}")
                return

            # Extract violations from evaluation
            violations = []
            if evaluation.llm_analysis and "violations" in evaluation.llm_analysis:
                violations = evaluation.llm_analysis["violations"]

            # Create sample
            sample = FineTuningSample(
                dataset_id=active_dataset.id,
                transcript_text=transcript.transcript_text,
                diarized_segments=transcript.diarized_segments,
                sentiment_analysis=transcript.sentiment_analysis,
                voice_baselines=getattr(transcript, 'voice_baselines', None),
                call_metadata={
                    "source": "human_review",
                    "evaluation_id": evaluation.id,
                    "ai_confidence": evaluation.confidence_score,
                    "duration_seconds": 300  # Placeholder
                },
                policy_template_id=evaluation.policy_template_id,
                expected_category_scores=review.human_category_scores,
                expected_violations=violations,
                expected_overall_score=review.human_overall_score,
                source_evaluation_id=evaluation.id,
                quality_score=review.ai_score_accuracy,
                difficulty_level="medium",  # Could be calculated
                split="train",
                used_in_training=False
            )
            db.add(sample)
            db.flush()

            # Update dataset statistics
            active_dataset.total_samples += 1
            active_dataset.training_samples += 1

            db.commit()
            logger.info(f"Added human review {review_id} to active dataset {active_dataset.id} as sample {sample.id}")

        except Exception as e:
            logger.error(f"Error adding review {review_id} to dataset: {e}")
            db.rollback()
            raise


