"""
Confidence Engine - 5-Signal Scoring Algorithm
MVP Evaluation Improvements - Phase 2
"""

import json
import logging
from typing import Dict, Any, List, Tuple, Optional
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class ConfidenceEngine:
    """
    5-signal confidence scoring algorithm for AI evaluations.
    Determines when evaluations need human review based on multiple quality indicators.
    """

    def __init__(self):
        # Configurable weights for the 5 signals
        self.weights = {
            "transcript_quality": 0.25,
            "llm_reproducibility": 0.25,
            "rule_llm_agreement": 0.20,
            "category_consistency": 0.20,
            "output_schema_valid": 0.10
        }

        # Thresholds for human review routing
        self.thresholds = {
            "high_confidence": 0.8,      # No review needed
            "medium_confidence": 0.5,    # Consider review
            "low_confidence": 0.5        # Human review required
        }

    def compute_confidence_score(
        self,
        transcript_confidence: Optional[float],
        llm_responses: List[Dict[str, Any]],
        rule_results: Dict[str, Any],
        category_scores: Dict[str, float],
        schema_valid: bool
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Compute overall confidence score using 5 signals.

        Args:
            transcript_confidence: Deepgram confidence score (0-1)
            llm_responses: List of LLM evaluation responses for reproducibility check
            rule_results: Deterministic rule engine results
            category_scores: AI-generated category scores
            schema_valid: Whether LLM response passed schema validation

        Returns:
            Tuple of (confidence_score, detailed_breakdown)
        """
        signals = {}

        # 1. Transcript Quality Signal
        signals["transcript_quality"] = self._compute_transcript_quality_signal(transcript_confidence)

        # 2. LLM Reproducibility Signal
        signals["llm_reproducibility"] = self._compute_reproducibility_signal(llm_responses)

        # 3. Rule-LLM Agreement Signal
        signals["rule_llm_agreement"] = self._compute_rule_agreement_signal(rule_results, category_scores)

        # 4. Category Consistency Signal
        signals["category_consistency"] = self._compute_category_consistency_signal(category_scores, rule_results)

        # 5. Schema Validity Signal
        signals["output_schema_valid"] = self._compute_schema_validity_signal(schema_valid)

        # Weighted sum
        confidence_score = sum(
            signals[signal_name] * weight
            for signal_name, weight in self.weights.items()
        )

        # Create detailed breakdown
        breakdown = {
            "confidence_score": round(confidence_score, 3),
            "signals": signals,
            "weights": self.weights,
            "requires_human_review": confidence_score < self.thresholds["low_confidence"],
            "confidence_level": self._get_confidence_level(confidence_score),
            "reasoning": self._generate_reasoning(signals, confidence_score)
        }

        logger.info(f"Confidence score computed: {confidence_score:.3f}, requires_review: {breakdown['requires_human_review']}")
        return confidence_score, breakdown

    def _compute_transcript_quality_signal(self, transcript_confidence: Optional[float]) -> float:
        """Signal 1: Transcript quality based on Deepgram confidence."""
        if transcript_confidence is None:
            return 0.5  # Neutral if no confidence available

        # Normalize confidence score (assuming Deepgram returns 0-1)
        # High confidence (>0.8) = high signal, low confidence (<0.6) = low signal
        if transcript_confidence >= 0.8:
            return 1.0
        elif transcript_confidence >= 0.6:
            return 0.7
        elif transcript_confidence >= 0.4:
            return 0.4
        else:
            return 0.1

    def _compute_reproducibility_signal(self, llm_responses: List[Dict[str, Any]]) -> float:
        """Signal 2: LLM reproducibility by comparing multiple runs."""
        if len(llm_responses) < 2:
            # If we only have one response, assume reproducibility for now
            # In production, we'd run LLM twice for each evaluation
            return 0.8

        try:
            # Compare overall scores
            scores = [resp.get("overall_score", 0) for resp in llm_responses]
            score_diff = abs(scores[0] - scores[1]) if len(scores) >= 2 else 0

            # Compare category scores similarity
            category_similarities = []
            if len(llm_responses) >= 2 and "category_scores" in llm_responses[0]:
                cats1 = llm_responses[0]["category_scores"]
                cats2 = llm_responses[1]["category_scores"]

                for category in set(cats1.keys()) | set(cats2.keys()):
                    score1 = cats1.get(category, 0)
                    score2 = cats2.get(category, 0)
                    diff = abs(score1 - score2)
                    similarity = max(0, 1.0 - (diff / 20.0))  # Normalize difference
                    category_similarities.append(similarity)

                avg_category_similarity = sum(category_similarities) / len(category_similarities) if category_similarities else 1.0

                # Combine score difference and category similarity
                score_similarity = max(0, 1.0 - (score_diff / 10.0))  # 10-point difference = 0 similarity
                reproducibility = (score_similarity + avg_category_similarity) / 2.0

                return min(1.0, reproducibility)
            else:
                # Fallback to score-only comparison
                score_similarity = max(0, 1.0 - (score_diff / 10.0))
                return score_similarity

        except Exception as e:
            logger.warning(f"Error computing reproducibility signal: {e}")
            return 0.5  # Neutral score on error

    def _compute_rule_agreement_signal(self, rule_results: Dict[str, Any], category_scores: Dict[str, float]) -> float:
        """Signal 3: Agreement between rule engine hits and LLM category scores."""
        if not rule_results or not category_scores:
            return 0.5

        try:
            agreements = []

            # Check greeting rule vs greeting category score
            if "greeting_within_15s" in rule_results:
                greeting_hit = rule_results["greeting_within_15s"].get("hit", False)
                greeting_score = category_scores.get("Greeting", category_scores.get("greeting", 50))

                # If rule says greeting missing but AI scores it high (>70), disagreement
                # If rule says greeting present but AI scores it low (<30), disagreement
                if greeting_hit and greeting_score < 30:
                    agreements.append(0.0)  # Disagreement
                elif not greeting_hit and greeting_score > 70:
                    agreements.append(0.0)  # Disagreement
                else:
                    agreements.append(1.0)  # Agreement

            # Check empathy rule vs empathy category score
            if "apology_or_empathy_present" in rule_results:
                empathy_hit = rule_results["apology_or_empathy_present"].get("hit", False)
                empathy_score = category_scores.get("Empathy", category_scores.get("empathy", 50))

                if empathy_hit and empathy_score < 40:
                    agreements.append(0.0)
                elif not empathy_hit and empathy_score > 80:
                    agreements.append(0.0)
                else:
                    agreements.append(1.0)

            # Check hold compliance rule vs professionalism score
            if "hold_compliance" in rule_results:
                hold_hit = rule_results["hold_compliance"].get("hit", False)
                prof_score = category_scores.get("Professionalism", category_scores.get("professionalism", 50))

                if not hold_hit and prof_score > 80:
                    agreements.append(0.0)  # High professionalism but hold rule failed
                else:
                    agreements.append(1.0)

            # Return average agreement if we have checks, otherwise neutral
            if agreements:
                return sum(agreements) / len(agreements)
            else:
                return 0.6  # Slightly positive if no specific rules to check

        except Exception as e:
            logger.warning(f"Error computing rule agreement signal: {e}")
            return 0.5

    def _compute_category_consistency_signal(self, category_scores: Dict[str, float], rule_results: Dict[str, Any]) -> float:
        """Signal 4: Logical consistency of category scores."""
        if not category_scores:
            return 0.5

        try:
            consistency_checks = []

            # Greeting score should be low if greeting rule failed
            greeting_score = category_scores.get("Greeting", category_scores.get("greeting"))
            if greeting_score is not None and "greeting_within_15s" in rule_results:
                greeting_rule_hit = rule_results["greeting_within_15s"].get("hit", False)
                if not greeting_rule_hit and greeting_score > 60:
                    consistency_checks.append(0.2)  # Inconsistent
                elif greeting_rule_hit and greeting_score < 30:
                    consistency_checks.append(0.2)  # Inconsistent
                else:
                    consistency_checks.append(1.0)

            # Professionalism should be low if multiple rules failed
            prof_score = category_scores.get("Professionalism", category_scores.get("professionalism"))
            if prof_score is not None:
                failed_rules = sum(1 for rule in rule_results.values() if not rule.get("hit", True))
                if failed_rules > 2 and prof_score > 70:
                    consistency_checks.append(0.3)  # Too high professionalism with many rule failures
                elif failed_rules == 0 and prof_score < 60:
                    consistency_checks.append(0.3)  # Too low professionalism when no rules failed
                else:
                    consistency_checks.append(1.0)

            # Overall score should roughly match average of category scores
            if len(category_scores) > 1:
                avg_category_score = sum(category_scores.values()) / len(category_scores)
                overall_score = category_scores.get("Overall", category_scores.get("overall_score"))
                if overall_score:
                    score_diff = abs(overall_score - avg_category_score)
                    if score_diff > 20:  # More than 20 points difference
                        consistency_checks.append(0.4)
                    else:
                        consistency_checks.append(1.0)

            # Return average consistency if we have checks
            if consistency_checks:
                return sum(consistency_checks) / len(consistency_checks)
            else:
                return 0.7  # Slightly positive if no consistency checks available

        except Exception as e:
            logger.warning(f"Error computing category consistency signal: {e}")
            return 0.5

    def _compute_schema_validity_signal(self, schema_valid: bool) -> float:
        """Signal 5: Schema validation result."""
        return 1.0 if schema_valid else 0.0

    def _get_confidence_level(self, confidence_score: float) -> str:
        """Convert confidence score to human-readable level."""
        if confidence_score >= self.thresholds["high_confidence"]:
            return "high"
        elif confidence_score >= self.thresholds["medium_confidence"]:
            return "medium"
        else:
            return "low"

    def _generate_reasoning(self, signals: Dict[str, float], confidence_score: float) -> str:
        """Generate human-readable reasoning for the confidence score."""
        reasons = []

        # Transcript quality
        if signals["transcript_quality"] < 0.5:
            reasons.append("low transcript confidence")
        elif signals["transcript_quality"] > 0.8:
            reasons.append("high transcript confidence")

        # Reproducibility
        if signals["llm_reproducibility"] < 0.7:
            reasons.append("inconsistent AI responses")
        elif signals["llm_reproducibility"] > 0.9:
            reasons.append("highly reproducible AI responses")

        # Rule agreement
        if signals["rule_llm_agreement"] < 0.5:
            reasons.append("AI scores disagree with rule checks")
        elif signals["rule_llm_agreement"] > 0.8:
            reasons.append("AI scores align with rule checks")

        # Category consistency
        if signals["category_consistency"] < 0.6:
            reasons.append("inconsistent category scores")
        elif signals["category_consistency"] > 0.8:
            reasons.append("logically consistent category scores")

        # Schema validity
        if not signals["output_schema_valid"]:
            reasons.append("invalid AI response format")

        if not reasons:
            reasons.append("all quality checks passed")

        reasoning = f"Confidence score {confidence_score:.2f}: " + ", ".join(reasons)
        return reasoning
