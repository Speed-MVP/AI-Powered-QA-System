"""
Detection Aggregator - Phase 5
Combines all detection results, collects evidence, aggregates confidence
"""

import logging
from typing import List, Dict, Any, Optional
from statistics import mean

logger = logging.getLogger(__name__)


class DetectionAggregator:
    """Aggregates detection results across multiple layers"""
    
    def aggregate_behavior_detection(
        self,
        exact_result: Optional[Dict[str, Any]],
        semantic_result: Optional[Dict[str, Any]],
        compliance_result: Dict[str, Any],
        deepgram_confidence: float = 1.0,
        utterance_count: int = 1
    ) -> Dict[str, Any]:
        """
        Aggregate detection results for a behavior
        
        Returns:
            Complete behavior detection result
        """
        # Determine best match
        best_match = None
        match_type = "none"
        confidence = 0.0
        
        if exact_result and exact_result.get("detected"):
            best_match = exact_result
            match_type = exact_result.get("match_type", "exact")
            confidence = exact_result.get("confidence", 1.0)
        elif semantic_result and semantic_result.get("detected"):
            best_match = semantic_result
            match_type = semantic_result.get("match_type", "semantic")
            confidence = semantic_result.get("confidence", 0.0)
        
        # Calculate weighted confidence
        final_confidence = self._calculate_confidence(
            confidence,
            deepgram_confidence,
            match_type,
            utterance_count
        )
        
        return {
            "detected": best_match is not None,
            "match_type": match_type,
            "matched_text": best_match.get("matched_text") if best_match else None,
            "confidence": final_confidence,
            "violation": compliance_result.get("violation", False),
            "violation_reason": compliance_result.get("violation_reason"),
            "timing_passed": compliance_result.get("timing_passed", True),
            "critical_violation": compliance_result.get("critical_violation", False),
            "evidence": {
                "exact_match": exact_result,
                "semantic_match": semantic_result,
                "deepgram_confidence": deepgram_confidence
            }
        }
    
    def _calculate_confidence(
        self,
        similarity_score: float,
        deepgram_confidence: float,
        match_type: str,
        evidence_strength: int
    ) -> float:
        """
        Calculate weighted confidence score
        
        Formula:
        confidence = 0.50 * similarity_score
                  + 0.20 * deepgram_confidence
                  + 0.20 * match_precision
                  + 0.10 * evidence_strength
        """
        match_precision = 1.0 if match_type == "exact" else 0.8
        evidence_factor = min(1.0, evidence_strength / 3.0)  # Normalize to 0-1
        
        confidence = (
            0.50 * similarity_score +
            0.20 * deepgram_confidence +
            0.20 * match_precision +
            0.10 * evidence_factor
        )
        
        return min(1.0, max(0.0, confidence))

