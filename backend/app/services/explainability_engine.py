"""
Explainability Engine
Phase 7: Generate human-readable explanations for scores, behaviors, and stages.
"""

import logging
from typing import Dict, Any, List
from statistics import mean

logger = logging.getLogger(__name__)


class ExplainabilityEngine:
    """
    Builds structured explanations for:
      - overall score
      - per-stage scores
      - per-behavior decisions
      - confidence breakdown
    """

    def build_explanation(
        self,
        final_evaluation: Dict[str, Any],
        detection_results: Dict[str, Any],
        llm_stage_evaluations: Dict[str, Any],
        confidence_breakdown: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Entry point: build full explanation payload."""
        stage_scores = final_evaluation.get("stage_scores", []) or []
        policy_violations = final_evaluation.get("policy_violations", []) or []

        overall_expl = self._build_overall_explanation(
            final_evaluation, stage_scores, policy_violations
        )
        stage_expls = self._build_stage_explanations(
            stage_scores, llm_stage_evaluations, detection_results
        )
        behavior_expls = self._build_behavior_explanations(
            llm_stage_evaluations, detection_results
        )
        confidence_expl = self._build_confidence_explanation(confidence_breakdown)

        explanation = {
            "overall_explanation": overall_expl,
            "stage_explanations": stage_expls,
            "behavior_explanations": behavior_expls,
            "confidence_explanation": confidence_expl,
        }

        return explanation

    # ---------------------- Overall Explanation ---------------------- #

    def _build_overall_explanation(
        self,
        final_evaluation: Dict[str, Any],
        stage_scores: List[Dict[str, Any]],
        policy_violations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        overall_score = final_evaluation.get("overall_score", 0)
        total_penalties = final_evaluation.get("total_penalties", 0)
        failure_reason = final_evaluation.get("failure_reason")

        contributions: List[Dict[str, Any]] = []
        for stage in stage_scores:
            stage_name = stage.get("stage_name") or stage.get("stage_id")
            score = stage.get("score", 0)
            weight = stage.get("weight", 0)
            contribution = (score * weight) / 100.0 if weight else 0.0
            contributions.append(
                {
                    "stage": stage_name,
                    "score": score,
                    "weight": weight,
                    "contribution": round(contribution, 2),
                }
            )

        penalties_brief = [
            {
                "rule_id": v.get("rule_id"),
                "severity": v.get("severity"),
                "description": v.get("description"),
                "penalty_points": next(
                    (
                        p.get("penalty_points", 0)
                        for p in final_evaluation.get("penalty_breakdown", [])
                        if p.get("rule_id") == v.get("rule_id")
                    ),
                    0,
                ),
            }
            for v in policy_violations
        ]

        breakdown = (
            "Score calculated as weighted average of stage scores, minus any penalties. "
            "Each stage's weight represents its contribution to the final score."
        )
        if total_penalties:
            breakdown += f" A total of {total_penalties:.1f} points were deducted due to policy violations."

        overall_explanation = {
            "score": overall_score,
            "breakdown": breakdown,
            "stage_contributions": contributions,
            "penalties": {"total": total_penalties, "breakdown": penalties_brief},
            "failure_reason": failure_reason,
        }
        return overall_explanation

    # ---------------------- Stage Explanations ---------------------- #

    def _build_stage_explanations(
        self,
        stage_scores: List[Dict[str, Any]],
        llm_stage_evaluations: Dict[str, Any],
        detection_results: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Explain why each stage received its score."""
        detection_by_behavior = {
            b.get("behavior_id"): b for b in detection_results.get("behaviors", [])
        }
        explanations: List[Dict[str, Any]] = []

        for stage in stage_scores:
            stage_id = stage.get("stage_id")
            stage_name = stage.get("stage_name") or stage_id
            score = stage.get("score", 0)
            weight = stage.get("weight", 0)
            stage_eval = llm_stage_evaluations.get(stage_id, {})
            behaviors = stage_eval.get("behaviors", [])

            behavior_breakdown: List[Dict[str, Any]] = []

            for beh in behaviors:
                beh_id = beh.get("behavior_id")
                beh_name = beh.get("behavior_name")
                satisfaction = beh.get("satisfaction_level", "none")
                beh_conf = beh.get("confidence", 0.5)

                det = detection_by_behavior.get(beh_id, {})
                detected = bool(det.get("detected", False) or satisfaction != "none")

                # Evidence from detection and LLM
                det_evidence = det.get("evidence")
                llm_evidence = beh.get("evidence", [])

                evidence_items: List[Dict[str, Any]] = []
                if isinstance(det_evidence, dict):
                    for key, val in det_evidence.items():
                        if val:
                            evidence_items.append({"source": key, "value": val})
                if isinstance(llm_evidence, list):
                    for item in llm_evidence:
                        evidence_items.append({"source": "llm", "value": item})

                impact = self._estimate_behavior_impact(stage, beh_id, satisfaction)
                reason = self._build_behavior_reason(
                    beh_name, detected, satisfaction, beh_conf
                )

                behavior_breakdown.append(
                    {
                        "behavior_id": beh_id,
                        "behavior": beh_name,
                        "detected": detected,
                        "satisfaction_level": satisfaction,
                        "confidence": beh_conf,
                        "impact": impact,
                        "reason": reason,
                        "evidence": evidence_items,
                    }
                )

            stage_reason = self._build_stage_reason(stage_name, score, behavior_breakdown)

            explanations.append(
                {
                    "stage_id": stage_id,
                    "stage_name": stage_name,
                    "score": score,
                    "weight": weight,
                    "explanation": stage_reason,
                    "behavior_breakdown": behavior_breakdown,
                }
            )

        return explanations

    def _estimate_behavior_impact(
        self, stage: Dict[str, Any], behavior_id: str, satisfaction_level: str
    ) -> str:
        """
        Heuristic: estimate impact of behavior on stage score.
        This is descriptive only (not re-running scoring).
        """
        weight = 0.0
        for beh in stage.get("behaviors", []):
            if beh.get("behavior_id") == behavior_id:
                weight = beh.get("weight", beh.get("raw_score", 0.0))
                break

        if satisfaction_level == "full":
            return f"Increased stage score by approximately {round(weight, 1)} points."
        elif satisfaction_level == "partial":
            return (
                f"Partially increased stage score (≈ {round(weight * 0.5, 1)} points)."
            )
        else:
            if weight:
                return f"Missing behavior likely reduced stage score by up to {round(weight, 1)} points."
            return "Minimal impact on stage score."

    def _build_behavior_reason(
        self, behavior_name: str, detected: bool, satisfaction_level: str, confidence: float
    ) -> str:
        if detected and satisfaction_level == "full":
            return f"Behavior '{behavior_name}' was clearly present with high confidence ({confidence:.2f})."
        if detected and satisfaction_level == "partial":
            return f"Behavior '{behavior_name}' was partially satisfied with moderate confidence ({confidence:.2f})."
        if not detected:
            return (
                f"Behavior '{behavior_name}' was not found in the transcript with sufficient evidence."
            )
        return f"Behavior '{behavior_name}' evaluation confidence: {confidence:.2f}."

    def _build_stage_reason(
        self, stage_name: str, score: float, behavior_breakdown: List[Dict[str, Any]]
    ) -> str:
        if not behavior_breakdown:
            return f"Stage '{stage_name}' scored {score}/100 with no mapped behaviors."

        satisfied = [
            b for b in behavior_breakdown if b.get("satisfaction_level") == "full"
        ]
        partial = [
            b for b in behavior_breakdown if b.get("satisfaction_level") == "partial"
        ]
        missing = [
            b for b in behavior_breakdown if b.get("satisfaction_level") == "none"
        ]

        parts = [f"Stage '{stage_name}' scored {score}/100."]
        if satisfied:
            names = ", ".join(b["behavior"] for b in satisfied[:3])
            parts.append(f"Key behaviors satisfied: {names}.")
        if partial:
            names = ", ".join(b["behavior"] for b in partial[:3])
            parts.append(f"Partially satisfied behaviors: {names}.")
        if missing:
            names = ", ".join(b["behavior"] for b in missing[:3])
            parts.append(f"Missing behaviors that reduced the score: {names}.")

        return " ".join(parts)

    # ---------------------- Behavior Explanations ---------------------- #

    def _build_behavior_explanations(
        self,
        llm_stage_evaluations: Dict[str, Any],
        detection_results: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Flattened list of behavior-level explanations."""
        detection_by_behavior = {
            b.get("behavior_id"): b for b in detection_results.get("behaviors", [])
        }
        explanations: List[Dict[str, Any]] = []

        for stage_id, stage_eval in llm_stage_evaluations.items():
            stage_name = stage_eval.get("stage_name") or stage_id
            for beh in stage_eval.get("behaviors", []):
                beh_id = beh.get("behavior_id")
                beh_name = beh.get("behavior_name")
                satisfaction = beh.get("satisfaction_level", "none")
                beh_conf = beh.get("confidence", 0.5)

                det = detection_by_behavior.get(beh_id, {})
                detected = bool(det.get("detected", False) or satisfaction != "none")

                det_evidence = det.get("evidence")
                llm_evidence = beh.get("evidence", [])
                evidence_items: List[Dict[str, Any]] = []
                if isinstance(det_evidence, dict):
                    for key, val in det_evidence.items():
                        if val:
                            evidence_items.append({"source": key, "value": val})
                if isinstance(llm_evidence, list):
                    for item in llm_evidence:
                        evidence_items.append({"source": "llm", "value": item})

                reason = self._build_behavior_reason(
                    beh_name, detected, satisfaction, beh_conf
                )

                explanations.append(
                    {
                        "stage_id": stage_id,
                        "stage_name": stage_name,
                        "behavior_id": beh_id,
                        "behavior_name": beh_name,
                        "detected": detected,
                        "satisfaction_level": satisfaction,
                        "confidence": beh_conf,
                        "reason": reason,
                        "evidence": evidence_items,
                    }
                )

        return explanations

    # ---------------------- Confidence Explanation ---------------------- #

    def _build_confidence_explanation(
        self, confidence_breakdown: Dict[str, Any]
    ) -> Dict[str, Any]:
        if not confidence_breakdown:
            return {
                "overall_confidence": None,
                "breakdown": {},
                "explanation": "Confidence breakdown not available.",
                "recommendations": [],
            }

        score = confidence_breakdown.get("confidence_score")
        signals = confidence_breakdown.get("signals", {})
        level = confidence_breakdown.get("confidence_level")

        recommendations: List[str] = []
        if signals.get("transcript_quality", 1.0) < 0.5:
            recommendations.append("Improve audio quality or transcription accuracy.")
        if signals.get("evidence_strength", 1.0) < 0.5:
            recommendations.append(
                "Add clearer, more explicit behaviors and phrases to the blueprint."
            )
        if signals.get("behavior_coverage", 1.0) < 0.5:
            recommendations.append(
                "Ensure each critical behavior has clear evidence in the transcript."
            )

        explanation = {
            "overall_confidence": score,
            "level": level,
            "breakdown": {k: round(v, 3) for k, v in signals.items()},
            "explanation": confidence_breakdown.get("reasoning"),
            "recommendations": recommendations,
        }
        return explanation






