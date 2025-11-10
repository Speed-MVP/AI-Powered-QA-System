"""
Confidence Calculation Service for Human Fallback Routing
Phase 1: Foundation - Confidence-based human fallback
"""

from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class ConfidenceService:
    """
    Service for calculating AI confidence scores and determining human review routing.
    Phase 1: confidence = (llm_confidence + avg_sentiment_confidence) / 2
    If confidence < 0.75: route_to_human_review()
    """

    def calculate_overall_confidence(
        self,
        llm_evaluation: Dict[str, Any],
        sentiment_analysis: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Calculate overall AI confidence score for human fallback routing.

        Formula: confidence = (llm_confidence + avg_sentiment_confidence) / 2
        """
        # Extract LLM confidence (0-1 scale)
        llm_confidence = self._extract_llm_confidence(llm_evaluation)

        # Calculate sentiment analysis confidence
        sentiment_confidence = self._calculate_sentiment_confidence(sentiment_analysis)

        # Calculate overall confidence
        if llm_confidence is not None and sentiment_confidence is not None:
            overall_confidence = (llm_confidence + sentiment_confidence) / 2
            # Be more honest about AI limitations - reduce confidence significantly
            overall_confidence = overall_confidence * 0.75  # Reduce by 25% to be more conservative
        elif llm_confidence is not None:
            overall_confidence = llm_confidence * 0.75  # Reduce by 25% to be more conservative
        else:
            overall_confidence = 0.3  # Even lower default confidence to be more honest

        # Determine if human review is required
        # Be more conservative - route more cases to human review to ensure quality
        requires_human_review = overall_confidence < 0.80  # More conservative threshold

        # Additional checks for critical violations
        has_critical_violations = self._check_critical_violations(llm_evaluation)
        if has_critical_violations:
            requires_human_review = True

        logger.info(
            f"Overall confidence: {overall_confidence:.3f}, "
            f"sentiment_confidence={sentiment_confidence:.3f}, "
            f"requires_human_review={requires_human_review}"
        )

        return {
            "confidence_score": overall_confidence,
            "llm_confidence": llm_confidence,
            "sentiment_confidence": sentiment_confidence,
            "requires_human_review": requires_human_review,
            "reason": self._get_human_review_reason(overall_confidence, has_critical_violations)
        }

    def _extract_llm_confidence(self, llm_evaluation: Dict[str, Any]) -> Optional[float]:
        """
        Extract confidence score from LLM evaluation response.
        Looks for explicit confidence fields or calculates based on evaluation quality.
        """
        # Check for explicit confidence field
        if "confidence" in llm_evaluation:
            confidence = llm_evaluation["confidence"]
            if isinstance(confidence, (int, float)) and 0 <= confidence <= 1:
                return float(confidence)

        # Check for llm_confidence field
        if "llm_confidence" in llm_evaluation:
            confidence = llm_evaluation["llm_confidence"]
            if isinstance(confidence, (int, float)) and 0 <= confidence <= 1:
                return float(confidence)

        # Fallback: Calculate confidence based on evaluation completeness
        # If LLM provided scores for all categories and no parsing errors, moderate confidence
        category_scores = llm_evaluation.get("category_scores", {})
        if category_scores and len(category_scores) > 0:
            # If we have category scores, assume moderate confidence (reduced from 0.7)
            return 0.6  # More realistic - AI evaluation has limitations
        else:
            # If parsing failed or incomplete, low confidence
            return 0.25  # Lower default for incomplete evaluations

    def _calculate_sentiment_confidence(self, sentiment_analysis: Optional[List[Dict[str, Any]]]) -> Optional[float]:
        """
        Calculate confidence in sentiment analysis quality.
        Higher confidence if we have comprehensive sentiment data from both speakers.
        """
        if not sentiment_analysis:
            return None

        # Check if we have sentiment data for both caller and agent
        speaker_types = set()
        total_segments = len(sentiment_analysis)

        for segment in sentiment_analysis:
            speaker = segment.get("speaker")
            if speaker:
                speaker_types.add(speaker)

        # Base confidence on coverage
        base_confidence = 0.4  # Lower base confidence (was 0.5) - sentiment analysis has limitations

        # Bonus for having both speakers
        if len(speaker_types) >= 2:
            base_confidence += 0.15  # Reduced bonus (was 0.2)

        # Bonus for having multiple segments per speaker
        segments_per_speaker = {}
        for segment in sentiment_analysis:
            speaker = segment.get("speaker", "unknown")
            segments_per_speaker[speaker] = segments_per_speaker.get(speaker, 0) + 1

        avg_segments = sum(segments_per_speaker.values()) / max(len(segments_per_speaker), 1)
        if avg_segments >= 3:  # At least 3 segments per speaker
            base_confidence += 0.15  # Reduced bonus (was 0.2)

        # Penalty for very few segments
        if total_segments < 3:
            base_confidence -= 0.15  # Reduced penalty (was 0.2)

        return max(0.2, min(0.8, base_confidence))  # Cap at 0.8 max (was 1.0) - sentiment analysis isn't perfect

    def _check_critical_violations(self, llm_evaluation: Dict[str, Any]) -> bool:
        """
        Check if there are critical policy violations that require human review.
        """
        violations = llm_evaluation.get("violations", [])

        critical_keywords = [
            "critical", "severe", "unacceptable", "major violation",
            "tone_mismatch", "disingenuous", "keyword_gaming"
        ]

        for violation in violations:
            severity = violation.get("severity", "").lower()
            violation_type = violation.get("type", "").lower()
            description = violation.get("description", "").lower()

            if (severity == "critical" or
                any(keyword in violation_type for keyword in critical_keywords) or
                any(keyword in description for keyword in critical_keywords)):
                return True

        return False

    def _get_human_review_reason(self, confidence: float, has_critical_violations: bool) -> str:
        """
        Generate human-readable reason for human review routing.
        """
        if has_critical_violations:
            return "Critical policy violations detected"
        elif confidence < 0.75:
            return ".2f"
        else:
            return "AI confidence sufficient - no human review required"
