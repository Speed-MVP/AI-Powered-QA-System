"""
Confidence Engine - Multi-Signal Scoring Algorithm
Phase 7: Enhanced confidence scoring for AI evaluations.
"""

import logging
from typing import Dict, Any, List, Tuple, Optional
from statistics import mean, pstdev

logger = logging.getLogger(__name__)


class ConfidenceEngine:
    """
    Multi-signal confidence scoring algorithm for AI evaluations.
    
    Signals (0-1 each):
      1) transcript_quality      - ASR confidence / completeness
      2) detection_agreement     - agreement across exact/semantic/hybrid matches
      3) llm_consistency         - stage_confidence + internal consistency
      4) rule_llm_agreement      - alignment between deterministic rules and LLM
      5) evidence_strength       - quantity / quality of evidence snippets
      6) stage_variance_factor   - low score variance across stages → higher confidence
      7) behavior_coverage       - percentage of behaviors with evidence
    """

    def __init__(self):
        # Configurable weights for the 7 signals (must sum to 1.0)
        self.weights = {
            "transcript_quality": 0.15,
            "detection_agreement": 0.20,
            "llm_consistency": 0.20,
            "rule_llm_agreement": 0.15,
            "evidence_strength": 0.15,
            "stage_variance_factor": 0.10,
            "behavior_coverage": 0.05,
        }

        # Thresholds for human review routing
        self.thresholds = {
            "high_confidence": 0.80,   # No review needed
            "medium_confidence": 0.60, # Show as \"borderline\"
            "low_confidence": 0.60     # < low_confidence ⇒ human review required
        }

    def compute_confidence_score(
        self,
        transcript_confidence: Optional[float],
        detection_results: Dict[str, Any],
        llm_stage_evaluations: Dict[str, Any],
        rule_results: Optional[Dict[str, Any]],
        stage_scores: List[Dict[str, Any]],
        schema_valid: bool
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Compute overall confidence score using multi-signal analysis.

        Args:
            transcript_confidence: ASR confidence score (0-1)
            detection_results: Detection engine output (behaviors, evidence)
            llm_stage_evaluations: LLM stage outputs with stage_confidence and behaviors
            rule_results: Deterministic rule engine results / policy_violations
            stage_scores: List of stage score dicts from scoring engine
            schema_valid: Whether LLM response passed schema validation

        Returns:
            Tuple of (confidence_score, detailed_breakdown)
        """
        signals: Dict[str, float] = {}

        signals["transcript_quality"] = self._compute_transcript_quality_signal(
            transcript_confidence
        )
        signals["detection_agreement"] = self._compute_detection_agreement_signal(
            detection_results
        )
        signals["llm_consistency"] = self._compute_llm_consistency_signal(
            llm_stage_evaluations
        )
        signals["rule_llm_agreement"] = self._compute_rule_agreement_signal(
            rule_results or {}, stage_scores
        )
        signals["evidence_strength"] = self._compute_evidence_strength_signal(
            detection_results, llm_stage_evaluations
        )
        signals["stage_variance_factor"] = self._compute_stage_variance_signal(
            stage_scores
        )
        signals["behavior_coverage"] = self._compute_behavior_coverage_signal(
            detection_results, llm_stage_evaluations
        )

        # Schema validity acts as a hard cap: if invalid, clamp confidence down
        schema_signal = 1.0 if schema_valid else 0.0

        # Weighted sum of signals
        confidence_score = sum(
            signals[name] * self.weights.get(name, 0.0)
            for name in signals.keys()
        )

        if not schema_valid:
            # If schema invalid, strongly reduce confidence (but keep some signal)
            confidence_score *= 0.4

        confidence_score = max(0.0, min(1.0, confidence_score))

        breakdown = {
            "confidence_score": round(confidence_score, 3),
            "signals": {k: round(v, 3) for k, v in signals.items()},
            "schema_valid": schema_valid,
            "schema_signal": schema_signal,
            "weights": self.weights,
            "requires_human_review": confidence_score < self.thresholds["low_confidence"],
            "confidence_level": self._get_confidence_level(confidence_score),
            "reasoning": self._generate_reasoning(signals, confidence_score, schema_valid),
        }

        logger.info(
            "Confidence score computed: %.3f (level=%s, requires_review=%s)",
            confidence_score,
            breakdown["confidence_level"],
            breakdown["requires_human_review"],
        )
        return confidence_score, breakdown

    def _compute_transcript_quality_signal(
        self, transcript_confidence: Optional[float]
    ) -> float:
        """Signal 1: Transcript quality based on ASR confidence."""
        if transcript_confidence is None:
            return 0.5  # Neutral if no confidence available

        # Normalize confidence score (assuming ASR returns 0-1)
        # High confidence (>0.8) = high signal, low confidence (<0.6) = low signal
        if transcript_confidence >= 0.8:
            return 1.0
        elif transcript_confidence >= 0.6:
            return 0.7
        elif transcript_confidence >= 0.4:
            return 0.4
        else:
            return 0.1

    def _compute_detection_agreement_signal(
        self, detection_results: Dict[str, Any]
    ) -> float:
        """
        Signal 2: Agreement across exact/semantic/hybrid detections.

        Heuristic:
          - Higher when many behaviors are detected with high confidence
          - Penalize when detections are extremely sparse or very low confidence
        """
        behaviors = detection_results.get("behaviors", []) or []
        if not behaviors:
            return 0.5

        confidences = [
            b.get("confidence", 0.0) for b in behaviors if b.get("detected", False)
        ]
        if not confidences:
            return 0.3  # No detections → low agreement

        avg_conf = sum(confidences) / len(confidences)
        detected_ratio = len(confidences) / max(len(behaviors), 1)

        # Combine average confidence and coverage
        score = 0.6 * avg_conf + 0.4 * detected_ratio
        return max(0.0, min(1.0, score))

    def _compute_llm_consistency_signal(
        self, llm_stage_evaluations: Dict[str, Any]
    ) -> float:
        """
        Signal 3: LLM consistency.

        Uses:
          - stage_confidence values
          - similarity of stage scores (not wildly different for similar stages)
        """
        if not llm_stage_evaluations:
            return 0.5

        stage_confs = []
        stage_scores = []

        for stage_id, stage_eval in llm_stage_evaluations.items():
            stage_confs.append(stage_eval.get("confidence", 0.5))
            stage_scores.append(stage_eval.get("stage_score", 0))

        if not stage_confs:
            return 0.5

        avg_conf = sum(stage_confs) / len(stage_confs)

        if len(stage_scores) > 1:
            # High variance in stage scores may indicate inconsistent evaluation
            variance = pstdev(stage_scores)
            # Normalize variance penalty (assuming 0-100 scores)
            variance_penalty = min(1.0, variance / 25.0)  # 25pts stddev => full penalty
            variance_factor = 1.0 - (0.7 * variance_penalty)
        else:
            variance_factor = 1.0

        score = max(0.0, min(1.0, avg_conf * variance_factor))
        return score

    def _compute_rule_agreement_signal(
        self, rule_results: Dict[str, Any], stage_scores: List[Dict[str, Any]]
    ) -> float:
        """
        Signal 4: Agreement between deterministic rules and scoring / stages.

        Heuristic:
          - If there are many critical/major violations but stages are scored very high,
            confidence should drop.
          - If no critical violations and stages are moderate/high, confidence is higher.
        """
        if not rule_results:
            return 0.7  # Slightly positive if no rules evaluated

        violations = rule_results.get("violations", []) or rule_results.get(
            "rule_evaluations", []
        )
        if not violations:
            return 0.8

        # Count severities
        critical = sum(1 for v in violations if v.get("severity") == "critical")
        major = sum(1 for v in violations if v.get("severity") == "major")
        minor = sum(1 for v in violations if v.get("severity") == "minor")

        avg_stage_score = (
            mean([s.get("score", 0) for s in stage_scores]) if stage_scores else 0.0
        )

        # Base on violation severity
        base = 1.0
        base -= min(0.6, critical * 0.25 + major * 0.1 + minor * 0.03)

        # If many severe violations but very high stage scores, reduce further
        if (critical + major) > 0 and avg_stage_score > 80:
            base -= 0.2

        return max(0.0, min(1.0, base))

    def _compute_evidence_strength_signal(
        self, detection_results: Dict[str, Any], llm_stage_evaluations: Dict[str, Any]
    ) -> float:
        """
        Signal 5: Evidence strength.

        Looks at:
          - How many behaviors have evidence attached
          - Number of evidence items per behavior / stage
        """
        behaviors = detection_results.get("behaviors", []) or []
        if not behaviors and not llm_stage_evaluations:
            return 0.4

        behavior_with_evidence = 0
        total_behaviors = len(behaviors)

        for b in behaviors:
            ev = b.get("evidence", {}) or {}
            # evidence may include exact_match / semantic_match etc.
            has_evidence = any(
                v for v in ev.values() if v is not None
            )
            if has_evidence:
                behavior_with_evidence += 1

        # Include LLM evidence as well
        llm_evidence_count = 0
        llm_behavior_count = 0
        for stage_eval in llm_stage_evaluations.values():
            for beh in stage_eval.get("behaviors", []):
                llm_behavior_count += 1
                ev_list = beh.get("evidence", [])
                if isinstance(ev_list, list) and ev_list:
                    llm_evidence_count += 1

        total_behavior_count = total_behaviors + llm_behavior_count
        total_with_evidence = behavior_with_evidence + llm_evidence_count

        if total_behavior_count == 0:
            return 0.5

        coverage = total_with_evidence / total_behavior_count
        # Evidence strength also scales with absolute count
        strength = min(1.0, coverage + (total_with_evidence / 20.0))
        return max(0.0, min(1.0, strength))

    def _compute_stage_variance_signal(
        self, stage_scores: List[Dict[str, Any]]
    ) -> float:
        """
        Signal 6: Stage variance factor.

        Large variance between stage scores can indicate brittle evaluation.
        """
        if not stage_scores or len(stage_scores) < 2:
            return 0.8

        scores = [s.get("score", 0.0) for s in stage_scores]
        variance = pstdev(scores)

        # 0 variance => 1.0, 20+ stddev => ~0.3
        penalty = min(1.0, variance / 20.0)
        factor = 1.0 - 0.7 * penalty
        return max(0.0, min(1.0, factor))

    def _compute_behavior_coverage_signal(
        self, detection_results: Dict[str, Any], llm_stage_evaluations: Dict[str, Any]
    ) -> float:
        """
        Signal 7: Behavior coverage.

        Measures how many defined behaviors were actually evaluated with a clear decision.
        """
        detected_behaviors = detection_results.get("behaviors", []) or []
        total_behaviors = len(detected_behaviors)

        if total_behaviors == 0 and llm_stage_evaluations:
            # Derive from LLM behaviors
            all_llm_behaviors = []
            for stage_eval in llm_stage_evaluations.values():
                all_llm_behaviors.extend(stage_eval.get("behaviors", []))
            total_behaviors = len(all_llm_behaviors)
            satisfied = sum(
                1
                for b in all_llm_behaviors
                if b.get("satisfaction_level") in ("full", "partial")
            )
        else:
            satisfied = sum(1 for b in detected_behaviors if b.get("detected", False))

        if total_behaviors == 0:
            return 0.5

        coverage = satisfied / total_behaviors
        # Small boost if many behaviors evaluated
        size_factor = min(1.0, total_behaviors / 10.0)
        score = max(0.0, min(1.0, 0.7 * coverage + 0.3 * size_factor))
        return score

    def _get_confidence_level(self, confidence_score: float) -> str:
        """Convert confidence score to human-readable level."""
        if confidence_score >= self.thresholds["high_confidence"]:
            return "high"
        elif confidence_score >= self.thresholds["medium_confidence"]:
            return "medium"
        else:
            return "low"

    def _generate_reasoning(
        self, signals: Dict[str, float], confidence_score: float, schema_valid: bool
    ) -> str:
        """Generate human-readable reasoning for the confidence score."""
        reasons: List[str] = []

        tq = signals.get("transcript_quality", 0.5)
        if tq < 0.5:
            reasons.append("low transcript confidence")
        elif tq > 0.8:
            reasons.append("high transcript confidence")

        da = signals.get("detection_agreement", 0.5)
        if da < 0.5:
            reasons.append("weak or inconsistent behavior detection")
        elif da > 0.8:
            reasons.append("strong agreement across detection methods")

        lc = signals.get("llm_consistency", 0.5)
        if lc < 0.5:
            reasons.append("LLM stage scores are inconsistent")
        elif lc > 0.8:
            reasons.append("LLM stage scores are consistent and confident")

        ra = signals.get("rule_llm_agreement", 0.5)
        if ra < 0.5:
            reasons.append("rule checks disagree with stage scores")
        elif ra > 0.8:
            reasons.append("rule checks align with stage scores")

        es = signals.get("evidence_strength", 0.5)
        if es < 0.5:
            reasons.append("limited evidence to support decisions")
        elif es > 0.8:
            reasons.append("strong evidence backing behavior decisions")

        sv = signals.get("stage_variance_factor", 0.5)
        if sv < 0.5:
            reasons.append("large variance between stage scores")

        bc = signals.get("behavior_coverage", 0.5)
        if bc < 0.5:
            reasons.append("many blueprint behaviors lack clear evaluation")

        if not schema_valid:
            reasons.append("LLM output failed schema validation (reduced confidence)")

        if not reasons:
            reasons.append("all quality checks passed")

        reasoning = f"Confidence score {confidence_score:.2f}: " + ", ".join(reasons)
        return reasoning
