"""
Continuous Learning Pipeline
MVP Evaluation Improvements - Phase 3

Collects human review data and uses it to improve AI evaluation quality through:
- Few-shot example curation
- Performance analytics
- Model improvement suggestions
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc

from app.models.human_review import HumanReview
from app.models.evaluation import Evaluation
from app.models.recording import Recording
from app.database import SessionLocal

logger = logging.getLogger(__name__)


class ContinuousLearningService:
    """
    Service for continuous learning from human reviews.
    Improves AI evaluation quality over time.
    """

    def __init__(self):
        self.db = SessionLocal()

    def collect_human_reviews_for_fine_tuning(
        self,
        days_back: int = 30,
        min_confidence_threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Collect human-reviewed evaluations suitable for fine-tuning.

        Args:
            days_back: How many days of data to collect
            min_confidence_threshold: Minimum AI confidence to include (focus on uncertain cases)

        Returns:
            List of fine-tuning examples with AI predictions and human corrections
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)

        # Query human reviews with their evaluations
        human_reviews = self.db.query(HumanReview).options(
            HumanReview.evaluation,
            HumanReview.evaluation.recording
        ).filter(
            and_(
                HumanReview.created_at >= cutoff_date,
                HumanReview.evaluation.has(),  # Has associated evaluation
                HumanReview.evaluation.confidence_score <= min_confidence_threshold  # Focus on uncertain cases
            )
        ).all()

        fine_tuning_examples = []

        for review in human_reviews:
            example = self._create_fine_tuning_example(review)
            if example:
                fine_tuning_examples.append(example)

        logger.info(f"Collected {len(fine_tuning_examples)} fine-tuning examples from {len(human_reviews)} human reviews")

        return fine_tuning_examples

    def _create_fine_tuning_example(self, human_review: HumanReview) -> Optional[Dict[str, Any]]:
        """
        Create a fine-tuning example from a human review.
        """
        try:
            evaluation = human_review.evaluation
            recording = evaluation.recording

            if not evaluation.llm_analysis or not recording or not recording.transcript:
                return None

            # Extract normalized transcript
            transcript_text = recording.transcript.transcript_text
            if hasattr(recording.transcript, 'normalized_text') and recording.transcript.normalized_text:
                transcript_text = recording.transcript.normalized_text

            # Create the example
            example = {
                "id": f"review_{human_review.id}",
                "recording_id": human_review.evaluation_id,
                "transcript": transcript_text,
                "ai_prediction": {
                    "overall_score": evaluation.overall_score,
                    "category_scores": evaluation.llm_analysis.get("category_scores", {}),
                    "violations": evaluation.llm_analysis.get("violations", []),
                    "resolution": evaluation.llm_analysis.get("resolution", "unknown"),
                    "confidence_score": evaluation.confidence_score
                },
                "human_correction": {
                    "overall_score": human_review.human_overall_score,
                    "category_scores": human_review.human_category_scores or {},
                    "violations": human_review.human_violations or [],
                    "reviewer_notes": human_review.reviewer_notes
                },
                "delta": human_review.delta or {},
                "metadata": {
                    "review_date": human_review.created_at.isoformat(),
                    "ai_model": evaluation.model_version,
                    "transcript_confidence": recording.transcript.transcription_confidence,
                    "call_duration": self._calculate_call_duration(recording.transcript.diarized_segments or [])
                }
            }

            return example

        except Exception as e:
            logger.warning(f"Failed to create fine-tuning example for review {human_review.id}: {e}")
            return None

    def _calculate_call_duration(self, segments: List[Dict]) -> Optional[float]:
        """Calculate total call duration from segments."""
        if not segments:
            return None

        start_time = min(s.get("start", 0) for s in segments)
        end_time = max(s.get("end", 0) for s in segments)
        return end_time - start_time

    def select_few_shot_examples(
        self,
        category: str,
        count: int = 3,
        min_delta: float = 5.0
    ) -> List[Dict[str, Any]]:
        """
        Select high-quality few-shot examples for prompt improvement.

        Args:
            category: Category to focus on (e.g., "Greeting", "Empathy")
            count: Number of examples to select
            min_delta: Minimum score difference to include

        Returns:
            List of few-shot examples
        """
        # Find reviews with significant delta in the specified category
        reviews_with_delta = self.db.query(HumanReview).filter(
            and_(
                HumanReview.human_category_scores.isnot(None),
                HumanReview.delta.isnot(None)
            )
        ).all()

        candidates = []

        for review in reviews_with_delta:
            delta = review.delta or {}
            category_deltas = delta.get("category_score_diffs", {})

            if category in category_deltas:
                delta_value = abs(category_deltas[category])
                if delta_value >= min_delta:
                    candidates.append((review, delta_value))

        # Sort by delta magnitude and take top examples
        candidates.sort(key=lambda x: x[1], reverse=True)
        selected_reviews = candidates[:count]

        examples = []
        for review, delta_score in selected_reviews:
            example = self._create_few_shot_example(review, category)
            if example:
                examples.append(example)

        logger.info(f"Selected {len(examples)} few-shot examples for category '{category}'")
        return examples

    def _create_few_shot_example(self, human_review: HumanReview, category: str) -> Optional[Dict[str, Any]]:
        """
        Create a concise few-shot example for prompt inclusion.
        """
        try:
            evaluation = human_review.evaluation
            recording = evaluation.recording

            if not recording or not recording.transcript:
                return None

            transcript = recording.transcript.transcript_text[:500]  # Limit length

            ai_score = evaluation.llm_analysis.get("category_scores", {}).get(category)
            human_score = human_review.human_category_scores.get(category) if human_review.human_category_scores else None

            if ai_score is None or human_score is None:
                return None

            example = {
                "transcript_snippet": transcript,
                "category": category,
                "ai_score": ai_score,
                "human_score": human_score,
                "correction_reason": human_review.reviewer_notes or "Score adjustment based on human review"
            }

            return example

        except Exception as e:
            logger.warning(f"Failed to create few-shot example: {e}")
            return None

    def analyze_performance_trends(self, days: int = 30) -> Dict[str, Any]:
        """
        Analyze performance trends over time.

        Returns:
            Performance metrics and trends
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Get all evaluations in time period
        evaluations = self.db.query(Evaluation).filter(
            Evaluation.created_at >= cutoff_date
        ).all()

        # Get human reviews in time period
        human_reviews = self.db.query(HumanReview).filter(
            HumanReview.created_at >= cutoff_date
        ).all()

        # Calculate metrics
        total_evaluations = len(evaluations)
        total_reviews = len(human_reviews)
        review_rate = total_reviews / total_evaluations if total_evaluations > 0 else 0

        # Confidence distribution
        confidence_levels = [e.confidence_score for e in evaluations if e.confidence_score is not None]
        avg_confidence = sum(confidence_levels) / len(confidence_levels) if confidence_levels else 0

        # Human-AI agreement analysis
        agreements = []
        for review in human_reviews:
            if review.human_overall_score is not None and review.evaluation.overall_score is not None:
                diff = abs(review.human_overall_score - review.evaluation.overall_score)
                agreement = 1.0 if diff <= 5 else 0.0  # Within 5 points = agreement
                agreements.append(agreement)

        avg_agreement = sum(agreements) / len(agreements) if agreements else 0

        # Category-level analysis
        category_performance = self._analyze_category_performance(human_reviews)

        analysis = {
            "time_period_days": days,
            "total_evaluations": total_evaluations,
            "total_human_reviews": total_reviews,
            "review_rate": review_rate,
            "average_confidence": avg_confidence,
            "human_ai_agreement": avg_agreement,
            "category_performance": category_performance,
            "generated_at": datetime.utcnow().isoformat()
        }

        logger.info(f"Performance analysis complete: {total_evaluations} evaluations, {total_reviews} reviews")
        return analysis

    def _analyze_category_performance(self, human_reviews: List[HumanReview]) -> Dict[str, Any]:
        """
        Analyze performance by category from human reviews.
        """
        category_stats = {}

        for review in human_reviews:
            if not review.human_category_scores or not review.evaluation.llm_analysis:
                continue

            ai_scores = review.evaluation.llm_analysis.get("category_scores", {})

            for category, human_score in review.human_category_scores.items():
                ai_score = ai_scores.get(category)

                if ai_score is not None:
                    if category not in category_stats:
                        category_stats[category] = {
                            "samples": 0,
                            "total_error": 0,
                            "agreements": 0
                        }

                    error = abs(ai_score - human_score)
                    agreement = 1 if error <= 5 else 0

                    category_stats[category]["samples"] += 1
                    category_stats[category]["total_error"] += error
                    category_stats[category]["agreements"] += agreement

        # Calculate averages
        for category, stats in category_stats.items():
            samples = stats["samples"]
            if samples > 0:
                stats["avg_error"] = stats["total_error"] / samples
                stats["agreement_rate"] = stats["agreements"] / samples
            del stats["total_error"]  # Clean up

        return category_stats

    def generate_model_improvement_suggestions(self, performance_analysis: Dict[str, Any]) -> List[str]:
        """
        Generate actionable suggestions for model improvement based on performance analysis.
        """
        suggestions = []

        # Review rate analysis
        review_rate = performance_analysis.get("review_rate", 0)
        if review_rate > 0.3:
            suggestions.append("High human review rate detected. Consider adjusting confidence thresholds or improving AI accuracy.")
        elif review_rate < 0.1:
            suggestions.append("Very low human review rate. Consider increasing review sampling for quality assurance.")

        # Agreement analysis
        agreement = performance_analysis.get("human_ai_agreement", 0)
        if agreement < 0.7:
            suggestions.append(f"Low human-AI agreement ({agreement:.2f}). Focus on fine-tuning with more human review examples.")

        # Category-specific suggestions
        category_performance = performance_analysis.get("category_performance", {})
        poor_categories = [
            cat for cat, stats in category_performance.items()
            if stats.get("avg_error", 0) > 10
        ]

        if poor_categories:
            suggestions.append(f"High error rates in categories: {', '.join(poor_categories)}. Consider category-specific prompt improvements.")

        # Confidence analysis
        avg_confidence = performance_analysis.get("average_confidence", 0)
        if avg_confidence < 0.5:
            suggestions.append(f"Low average confidence ({avg_confidence:.2f}). Review confidence engine calibration.")

        return suggestions

    def export_training_dataset(self, output_path: str, days_back: int = 90) -> int:
        """
        Export comprehensive training dataset for model fine-tuning.

        Args:
            output_path: Path to save the JSON dataset
            days_back: How many days of data to include

        Returns:
            Number of examples exported
        """
        examples = self.collect_human_reviews_for_fine_tuning(days_back=days_back, min_confidence_threshold=1.0)

        # Add metadata
        dataset = {
            "metadata": {
                "created_at": datetime.utcnow().isoformat(),
                "days_back": days_back,
                "total_examples": len(examples),
                "version": "1.0"
            },
            "examples": examples
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, default=str)

        logger.info(f"Exported {len(examples)} training examples to {output_path}")
        return len(examples)

    def get_weekly_report(self) -> Dict[str, Any]:
        """
        Generate weekly performance report.
        """
        # Analyze last 7 days
        analysis = self.analyze_performance_trends(days=7)
        suggestions = self.generate_model_improvement_suggestions(analysis)

        report = {
            "report_type": "weekly_performance",
            "analysis": analysis,
            "suggestions": suggestions,
            "generated_at": datetime.utcnow().isoformat()
        }

        return report