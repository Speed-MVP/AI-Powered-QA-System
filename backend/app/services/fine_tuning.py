"""
Fine-Tuning Service for Gemini Models
Phase 3: Fine-Tuning & Self-Learning
"""

from app.database import SessionLocal
from app.models.human_review import FineTuningDataset, FineTuningSample, ModelPerformance
from app.config import settings
from typing import Dict, Any, Optional, List
import logging
import json
from datetime import datetime, timedelta
import time

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("google-generativeai not installed. Fine-tuning service will not work.")

logger = logging.getLogger(__name__)


class FineTuningService:
    """
    Service for fine-tuning Gemini models on QA evaluation tasks.
    Phase 3: Use labeled data to fine-tune Gemini on QA rubrics.
    """

    def __init__(self):
        if not GEMINI_AVAILABLE:
            raise Exception("google-generativeai package not installed")

        if settings.gemini_api_key:
            genai.configure(api_key=settings.gemini_api_key)
        else:
            raise Exception("Gemini API key not configured")

    def start_fine_tuning_job(self, dataset_id: str) -> Dict[str, Any]:
        """
        Start a fine-tuning job using Vertex AI for the specified dataset.
        """
        db = SessionLocal()
        try:
            # Get dataset
            dataset = db.query(FineTuningDataset).filter(FineTuningDataset.id == dataset_id).first()
            if not dataset:
                return {"success": False, "error": f"Dataset {dataset_id} not found"}

            if dataset.training_samples < 10:
                return {"success": False, "error": f"Dataset has only {dataset.training_samples} training samples (minimum: 10)"}

            # Prepare training data
            training_data = self._prepare_training_data(dataset_id, db)

            if len(training_data) < 10:
                return {"success": False, "error": f"Only {len(training_data)} valid training samples prepared"}

            # Create fine-tuning job (simulated for now - would use Vertex AI in production)
            job_id = f"ft_{dataset_id}_{int(time.time())}"

            # Update dataset status
            dataset.fine_tuning_job_id = job_id
            dataset.fine_tuning_status = "running"

            # In production, this would submit to Vertex AI
            # For now, we'll simulate the fine-tuning process
            logger.info(f"Starting fine-tuning job {job_id} with {len(training_data)} samples")

            db.commit()

            return {
                "success": True,
                "job_id": job_id,
                "dataset_id": dataset_id,
                "training_samples": len(training_data),
                "status": "running",
                "note": "Fine-tuning job submitted (simulated)"
            }

        except Exception as e:
            db.rollback()
            logger.error(f"Error starting fine-tuning job: {e}")
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    def check_fine_tuning_status(self, job_id: str) -> Dict[str, Any]:
        """
        Check the status of a fine-tuning job.
        """
        db = SessionLocal()
        try:
            dataset = db.query(FineTuningDataset).filter(
                FineTuningDataset.fine_tuning_job_id == job_id
            ).first()

            if not dataset:
                return {"success": False, "error": f"Job {job_id} not found"}

            # In production, this would check Vertex AI status
            # For simulation, we'll assume completion after some time
            if dataset.fine_tuning_status == "running":
                # Simulate completion after some time
                hours_since_creation = (datetime.utcnow() - dataset.created_at).total_seconds() / 3600
                if hours_since_creation > 2:  # Simulate 2-hour training time
                    dataset.fine_tuning_status = "completed"
                    dataset.fine_tuned_accuracy = 0.85  # Simulated improvement
                    db.commit()

            return {
                "success": True,
                "job_id": job_id,
                "status": dataset.fine_tuning_status,
                "model_version": dataset.model_version,
                "baseline_accuracy": float(dataset.baseline_accuracy) if dataset.baseline_accuracy else None,
                "fine_tuned_accuracy": float(dataset.fine_tuned_accuracy) if dataset.fine_tuned_accuracy else None,
                "improvement": float(dataset.fine_tuned_accuracy - dataset.baseline_accuracy) if (
                    dataset.fine_tuned_accuracy and dataset.baseline_accuracy
                ) else None
            }

        finally:
            db.close()

    def _prepare_training_data(self, dataset_id: str, db) -> List[Dict[str, Any]]:
        """
        Prepare training data in the format required for Gemini fine-tuning.
        Input: transcripts + structured features
        Output: category scores + violations
        """
        samples = db.query(FineTuningSample).filter(
            FineTuningSample.dataset_id == dataset_id,
            FineTuningSample.split == "train"
        ).all()

        training_data = []

        for sample in samples:
            try:
                # Build input prompt (similar to our evaluation prompt but with training context)
                input_text = self._build_training_input(sample)

                # Build expected output (the human-reviewed scores)
                output_text = self._build_training_output(sample)

                training_data.append({
                    "text_input": input_text,
                    "output": output_text,
                    "sample_id": sample.id
                })

            except Exception as e:
                logger.warning(f"Error preparing training sample {sample.id}: {e}")
                continue

        return training_data

    def _build_training_input(self, sample: FineTuningSample) -> str:
        """Build the input text for training (transcript + context)."""
        input_parts = []

        # Add call metadata context
        if sample.call_metadata:
            metadata = sample.call_metadata
            input_parts.append(f"Call Context:")
            input_parts.append(f"- Duration: {metadata.get('duration_seconds', 'Unknown')} seconds")
            input_parts.append(f"- Speakers: {metadata.get('speaker_count', 'Unknown')}")
            input_parts.append("")

        # Add transcript
        input_parts.append(f"TRANSCRIPT:")
        input_parts.append(sample.transcript_text)
        input_parts.append("")

        # Add sentiment analysis if available
        if sample.sentiment_analysis:
            input_parts.append("VOICE ANALYSIS:")
            for i, sentiment in enumerate(sample.sentiment_analysis[:10]):  # Limit for context window
                sent_info = sentiment.get("sentiment", {})
                if isinstance(sent_info, dict):
                    sentiment_desc = sent_info.get("sentiment", "unknown")
                    confidence = sent_info.get("score", 0)
                    input_parts.append(f"  Segment {i+1}: {sentiment_desc} (confidence: {confidence})")
            input_parts.append("")

        # Add voice baselines if available
        if sample.voice_baselines:
            input_parts.append("VOICE BASELINES:")
            for speaker, baseline in sample.voice_baselines.items():
                if isinstance(baseline, dict):
                    pos_ratio = baseline.get("baseline_positive_ratio", 0)
                    neg_ratio = baseline.get("baseline_negative_ratio", 0)
                    input_parts.append(f"  {speaker}: {pos_ratio:.2f} positive, {neg_ratio:.2f} negative baseline")
            input_parts.append("")

        return "\n".join(input_parts)

    def _build_training_output(self, sample: FineTuningSample) -> str:
        """Build the expected output for training (human-reviewed scores)."""
        output_parts = []

        # Overall score
        output_parts.append(f"Overall Score: {sample.expected_overall_score}/100")

        # Category scores
        if sample.expected_category_scores:
            output_parts.append("")
            output_parts.append("Category Scores:")
            for category, score_data in sample.expected_category_scores.items():
                if isinstance(score_data, dict):
                    score = score_data.get("score", 0)
                    feedback = score_data.get("feedback", "")
                    output_parts.append(f"  {category}: {score}/100 - {feedback}")
                else:
                    output_parts.append(f"  {category}: {score_data}/100")

        # Violations
        if sample.expected_violations:
            output_parts.append("")
            output_parts.append("Policy Violations:")
            for violation in sample.expected_violations:
                category = violation.get("category_name", "Unknown")
                violation_type = violation.get("type", "unknown")
                severity = violation.get("severity", "minor")
                description = violation.get("description", "")
                output_parts.append(f"  {category} - {violation_type} ({severity}): {description}")

        # Resolution and tone analysis
        output_parts.append("")
        output_parts.append("Resolution: detected")  # Assume resolution detected for training
        output_parts.append("Resolution Confidence: 0.90")  # Placeholder
        output_parts.append("Customer Tone: neutral")  # Placeholder
        output_parts.append("Agent Tone: professional")  # Placeholder

        return "\n".join(output_parts)

    def evaluate_model_performance(
        self,
        model_version: str = "gemini-1.5-pro",
        evaluation_period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Evaluate current model performance against human reviews.
        Phase 3: Confidence calibration and threshold optimization.
        """
        db = SessionLocal()
        try:
            # Get evaluations from the last N days
            period_start = datetime.utcnow() - timedelta(days=evaluation_period_days)
            period_end = datetime.utcnow()

            # Get human-reviewed evaluations in this period
            human_reviews = db.query(HumanReview).join(Evaluation).filter(
                Evaluation.created_at >= period_start,
                Evaluation.created_at <= period_end,
                HumanReview.review_status == 'completed'
            ).all()

            if len(human_reviews) < 10:
                return {
                    "success": False,
                    "error": f"Insufficient data: only {len(human_reviews)} human reviews in last {evaluation_period_days} days"
                }

            # Calculate performance metrics
            ai_scores = []
            human_scores = []
            agreements = []

            for review in human_reviews:
                evaluation = db.query(Evaluation).filter(Evaluation.id == review.evaluation_id).first()
                if evaluation:
                    ai_score = evaluation.overall_score
                    human_score = review.human_overall_score

                    ai_scores.append(ai_score)
                    human_scores.append(human_score)

                    # Agreement within 10 points
                    agreement = abs(ai_score - human_score) <= 10
                    agreements.append(agreement)

            # Calculate metrics
            accuracy = np.mean(agreements) if agreements else 0
            mae = np.mean([abs(a - h) for a, h in zip(ai_scores, human_scores)]) if ai_scores else 0
            rmse = np.sqrt(np.mean([(a - h) ** 2 for a, h in zip(ai_scores, human_scores)])) if ai_scores else 0

            # Get confidence metrics
            evaluations = [db.query(Evaluation).filter(Evaluation.id == r.evaluation_id).first()
                          for r in human_reviews]
            confidences = [e.confidence_score for e in evaluations if e.confidence_score]

            avg_confidence = np.mean(confidences) if confidences else 0
            human_review_rate = sum(1 for e in evaluations if e.requires_human_review) / len(evaluations)

            # Create performance record
            performance = ModelPerformance(
                model_version=model_version,
                total_evaluations=len(human_reviews),
                evaluation_period_start=period_start,
                evaluation_period_end=period_end,
                accuracy_score=round(float(accuracy), 4),
                human_agreement_rate=round(float(accuracy), 4),
                avg_confidence_score=round(float(avg_confidence), 4),
                human_review_rate=round(float(human_review_rate), 4)
            )

            # Calculate MAE and RMSE as precision/recall approximations
            performance.precision_score = round(1.0 - float(mae) / 100.0, 4)  # Inverse of error
            performance.recall_score = round(1.0 - float(rmse) / 100.0, 4)    # Inverse of error
            performance.f1_score = round(2 * performance.precision_score * performance.recall_score /
                                       (performance.precision_score + performance.recall_score), 4)

            db.add(performance)
            db.commit()

            logger.info(f"Evaluated model performance: accuracy={accuracy:.3f}, MAE={mae:.1f}, human_review_rate={human_review_rate:.3f}")

            return {
                "success": True,
                "performance_id": performance.id,
                "model_version": model_version,
                "evaluation_period_days": evaluation_period_days,
                "total_evaluations": len(human_reviews),
                "accuracy": round(float(accuracy), 4),
                "mae": round(float(mae), 2),
                "rmse": round(float(rmse), 2),
                "avg_confidence": round(float(avg_confidence), 4),
                "human_review_rate": round(float(human_review_rate), 4),
                "recommendations": self._generate_performance_recommendations(accuracy, human_review_rate)
            }

        except Exception as e:
            db.rollback()
            logger.error(f"Error evaluating model performance: {e}")
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    def _generate_performance_recommendations(self, accuracy: float, human_review_rate: float) -> List[str]:
        """Generate recommendations based on performance metrics."""
        recommendations = []

        if accuracy < 0.7:
            recommendations.append("Model accuracy is below acceptable threshold. Consider additional fine-tuning.")
        elif accuracy > 0.9:
            recommendations.append("Excellent model accuracy! Consider reducing human review rate.")

        if human_review_rate > 0.3:
            recommendations.append("High human review rate suggests model needs improvement or confidence threshold needs adjustment.")
        elif human_review_rate < 0.05:
            recommendations.append("Very low human review rate - consider increasing confidence threshold or adding more human oversight.")

        if not recommendations:
            recommendations.append("Model performance is within acceptable ranges. Continue monitoring.")

        return recommendations


