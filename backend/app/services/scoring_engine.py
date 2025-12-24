"""
Scoring Engine - Phase 7
Deterministic scoring algorithm for evaluations
"""

import logging
from typing import Dict, Any, List, Optional
from decimal import Decimal
from statistics import mean

logger = logging.getLogger(__name__)


class ScoringEngine:
    """Scoring engine for evaluations"""
    
    def __init__(self, alpha: float = 0.6):
        """
        Args:
            alpha: Confidence floor (0-1). Prevents tiny confidences from zeroing scores.
        """
        self.alpha = alpha
    
    def compute_evaluation(
        self,
        llm_stage_evaluations: Dict[str, Any],
        detection_results: Dict[str, Any],
        compiled_rubric: Dict[str, Any],
        policy_rule_results: Optional[Dict[str, Any]] = None,
        company_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Compute final evaluation score
        
        Args:
            llm_stage_evaluations: Per-stage LLM evaluation results
            detection_results: Detection engine results
            compiled_rubric: Rubric template with categories and mappings
            policy_rule_results: Policy rule violations
            company_config: Company scoring configuration
        
        Returns:
            Final evaluation snapshot
        """
        logger.info("SCORING_ENGINE: Starting evaluation computation")
        company_config = company_config or {}
        
        # Log input summary
        num_stages = len(llm_stage_evaluations)
        num_behaviors = sum(len(s.get("behaviors", [])) for s in llm_stage_evaluations.values())
        num_categories = len(compiled_rubric.get("categories", []))
        num_mappings = len(compiled_rubric.get("mappings", []))
        logger.debug(f"SCORING_INPUT: {num_stages} stages, {num_behaviors} behaviors, "
                    f"{num_categories} rubric categories, {num_mappings} mappings")
        
        # Step A: Normalize weights
        self._normalize_weights(compiled_rubric)
        
        # Step B: Compute per-behavior scores
        behavior_scores = self._compute_behavior_scores(
            llm_stage_evaluations,
            detection_results,
            compiled_rubric
        )
        logger.debug(f"SCORING_STEP_B: Computed {len(behavior_scores)} behavior scores")
        
        # Log behavior score details
        for beh_id, beh_data in behavior_scores.items():
            logger.debug(f"  BEHAVIOR_SCORE: '{beh_data.get('behavior_name')}' - "
                        f"satisfaction={beh_data.get('satisfaction_level')}, "
                        f"weight={beh_data.get('weight'):.1f}, "
                        f"raw_score={beh_data.get('raw_score'):.1f}")
        
        # Step C: Apply confidence adjustment
        behavior_scores = self._apply_confidence_adjustment(behavior_scores, company_config)
        
        # Step D: Aggregate stage scores
        stage_scores = self._aggregate_stage_scores(behavior_scores, compiled_rubric)
        logger.debug(f"SCORING_STEP_D: Aggregated {len(stage_scores)} stage scores")
        
        # Log stage score details
        for stage in stage_scores:
            logger.info(f"  STAGE_SCORE: '{stage.get('stage_name')}' - "
                       f"score={stage.get('score')}, weight={stage.get('weight'):.1f}, "
                       f"confidence={stage.get('confidence'):.2f}")
        
        # Step E: Apply penalties
        total_penalties = 0
        penalty_breakdown = []
        if policy_rule_results:
            total_penalties, penalty_breakdown = self._apply_penalties(
                policy_rule_results,
                company_config
            )
            if total_penalties > 0:
                logger.info(f"SCORING_PENALTIES: Applied {total_penalties} penalty points from {len(penalty_breakdown)} violations")
        
        # Step F: Calculate overall score
        overall_score = self._calculate_overall_score(stage_scores, total_penalties)
        
        # Step G: Determine pass/fail
        overall_passed, failure_reason = self._determine_pass_fail(
            overall_score,
            stage_scores,
            policy_rule_results,
            company_config
        )
        
        # Step H: Determine if human review required
        requires_human_review = self._requires_human_review(
            stage_scores,
            policy_rule_results,
            company_config
        )
        
        # Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence(stage_scores)
        
        # Log final summary
        logger.info(f"SCORING_RESULT: overall_score={round(overall_score)}, "
                   f"passed={overall_passed}, confidence={overall_confidence:.2f}, "
                   f"penalties={total_penalties}, requires_review={requires_human_review}")
        if failure_reason:
            logger.info(f"SCORING_RESULT: failure_reason={failure_reason}")
        
        return {
            "overall_score": round(overall_score),
            "overall_passed": overall_passed,
            "failure_reason": failure_reason,
            "requires_human_review": requires_human_review,
            "confidence_score": overall_confidence,
            "total_penalties": total_penalties,
            "penalty_breakdown": penalty_breakdown,
            "policy_violations": policy_rule_results.get("violations", []) if policy_rule_results else [],
            "stage_scores": stage_scores,
            "behavior_scores": behavior_scores,
            "created_at": None  # Will be set by caller
        }
    
    def _normalize_weights(self, rubric: Dict[str, Any]):
        """Normalize stage and behavior weights"""
        categories = rubric.get("categories", [])
        if not categories:
            return
        
        # Normalize category weights to sum to 100
        total_weight = sum(cat.get("weight", 0) for cat in categories)
        if total_weight > 0 and abs(total_weight - 100.0) > 0.01:
            for cat in categories:
                cat["weight"] = (cat.get("weight", 0) / total_weight) * 100
    
    def _compute_behavior_scores(
        self,
        llm_evaluations: Dict[str, Any],
        detection_results: Dict[str, Any],
        rubric: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """Compute per-behavior numeric scores"""
        behavior_scores = {}
        mappings = rubric.get("mappings", [])
        
        # Map behavior_id to contribution_weight
        behavior_weights = {}
        for mapping in mappings:
            step_id = mapping.get("flow_step_id")
            weight = mapping.get("contribution_weight", 0)
            behavior_weights[step_id] = weight
        
        logger.debug(f"SCORING_WEIGHTS: Loaded {len(behavior_weights)} behavior weight mappings")
        if not behavior_weights:
            logger.warning("SCORING_WEIGHTS: No behavior weight mappings found in rubric! All scores will be 0.")
        
        # Track behaviors without weights for debugging
        missing_weights = []
        
        # Process LLM evaluations
        for stage_id, stage_eval in llm_evaluations.items():
            behaviors = stage_eval.get("behaviors", [])
            stage_name = stage_eval.get("stage_name")
            for behavior in behaviors:
                behavior_id = behavior.get("behavior_id")
                satisfaction_level = behavior.get("satisfaction_level", "none")
                confidence = behavior.get("confidence", 0.5)
                
                # Map satisfaction to multiplier
                if satisfaction_level == "full":
                    multiplier = 1.0
                elif satisfaction_level == "partial":
                    multiplier = 0.5
                else:
                    multiplier = 0.0
                
                # Get behavior weight
                weight = behavior_weights.get(behavior_id, 0)
                
                # Track missing weights
                if weight == 0 and behavior_id not in behavior_weights:
                    missing_weights.append(behavior.get("behavior_name", behavior_id))
                
                # Calculate raw score
                raw_score = weight * multiplier
                
                behavior_scores[behavior_id] = {
                    "behavior_id": behavior_id,
                    "behavior_name": behavior.get("behavior_name", ""),
                    "raw_score": raw_score,
                    "effective_score": raw_score,  # Will be adjusted by confidence
                    "weight": weight,
                    "satisfaction_level": satisfaction_level,
                    "confidence": confidence,
                    "stage_id": stage_id,
                    # Preserve human-readable stage name for downstream aggregation
                    "stage_name": stage_name,
                }
        
        # Log warning about missing weights
        if missing_weights:
            logger.warning(f"SCORING_WEIGHTS: {len(missing_weights)} behaviors have no weight mapping: {missing_weights[:5]}{'...' if len(missing_weights) > 5 else ''}")
        
        return behavior_scores
    
    def _apply_confidence_adjustment(
        self,
        behavior_scores: Dict[str, Dict[str, Any]],
        company_config: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """Apply confidence-based score adjustment"""
        enable_confidence_weighting = company_config.get("enable_confidence_weighting", False)
        alpha = company_config.get("alpha", self.alpha)
        
        if not enable_confidence_weighting:
            return behavior_scores
        
        for behavior_id, score_data in behavior_scores.items():
            confidence = score_data.get("confidence", 0.5)
            raw_score = score_data.get("raw_score", 0)
            
            # Apply confidence multiplier
            multiplier = alpha + (1 - alpha) * confidence
            effective_score = raw_score * multiplier
            
            score_data["effective_score"] = effective_score
        
        return behavior_scores
    
    def _aggregate_stage_scores(
        self,
        behavior_scores: Dict[str, Dict[str, Any]],
        rubric: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Aggregate behavior scores into stage scores"""
        stage_scores_by_id: Dict[str, Dict[str, Any]] = {}
        categories = rubric.get("categories", []) or []

        # Build a lookup of category weights by display name (stage name)
        category_by_name: Dict[str, Dict[str, Any]] = {
            c.get("name"): c for c in categories if c.get("name")
        }

        # Group behaviors by stage_id while preserving stage_name
        for _behavior_id, score_data in behavior_scores.items():
            stage_id = score_data.get("stage_id")
            if not stage_id:
                continue

            stage_entry = stage_scores_by_id.setdefault(stage_id, {
                "stage_id": stage_id,
                "stage_name": score_data.get("stage_name") or stage_id,
                "behaviors": [],
                "total_score": 0.0,
                "total_weight": 0.0,
                "confidence_scores": [],
            })

            stage_entry["behaviors"].append(score_data)
            stage_entry["total_score"] += score_data.get("effective_score", 0)
            stage_entry["total_weight"] += score_data.get("weight", 0)
            stage_entry["confidence_scores"].append(score_data.get("confidence", 0.5))

        result: List[Dict[str, Any]] = []

        if categories:
            # Preserve rubric category ordering, but map scores using stage_name
            for category in categories:
                stage_name = category.get("name")
                matching_stage = None

                # Find the stage whose human-readable name matches this category
                if stage_name:
                    for s in stage_scores_by_id.values():
                        if s.get("stage_name") == stage_name:
                            matching_stage = s
                            break

                if not matching_stage:
                    # No behaviors mapped to this category yet; still expose it with zero score
                    stage_id = category.get("id")
                    score = 0.0
                    confidence_scores: List[float] = []
                    total_weight = 0.0
                else:
                    stage_id = matching_stage.get("stage_id")
                    total_score = matching_stage.get("total_score", 0.0)
                    total_weight = matching_stage.get("total_weight", 0.0)
                    confidence_scores = matching_stage.get("confidence_scores", [])
                    
                    # Calculate stage score as percentage (0-100)
                    # If total_weight is 0, score is 0 (no behaviors in this stage)
                    if total_weight > 0:
                        score = (total_score / total_weight) * 100.0
                    else:
                        score = 0.0

                stage_weight = category.get("weight", 0)
                stage_confidence = mean(confidence_scores or [0.5])

                # Attach behaviors when we have a matching stage so the UI can show them
                behaviors = matching_stage.get("behaviors", []) if matching_stage else []

                result.append({
                    "stage_id": stage_id,
                    "stage_name": stage_name,
                    "score": round(score),
                    "weight": stage_weight,
                    "confidence": stage_confidence,
                    "behaviors": behaviors,
                })
        else:
            # Fallback: no rubric categories; derive equal weights from stages we observed
            num_stages = len(stage_scores_by_id)
            default_weight = 100.0 / num_stages if num_stages > 0 else 0.0

            for stage_id, stage_data in stage_scores_by_id.items():
                stage_name = stage_data.get("stage_name") or stage_id
                total_score = stage_data.get("total_score", 0.0)
                total_weight = stage_data.get("total_weight", 0.0)
                confidence_scores = stage_data.get("confidence_scores", [])
                stage_confidence = mean(confidence_scores or [0.5])
                
                # Calculate stage score as percentage (0-100)
                if total_weight > 0:
                    score = (total_score / total_weight) * 100.0
                else:
                    score = 0.0

                result.append({
                    "stage_id": stage_id,
                    "stage_name": stage_name,
                    "score": round(score),
                    "weight": default_weight,
                    "confidence": stage_confidence,
                    "behaviors": stage_data.get("behaviors", []),
                })

        return result
    
    def _apply_penalties(
        self,
        policy_rule_results: Dict[str, Any],
        company_config: Dict[str, Any]
    ) -> tuple[float, List[Dict[str, Any]]]:
        """Apply penalties from policy rule violations"""
        total_penalties = 0.0
        penalty_breakdown = []
        
        violations = policy_rule_results.get("violations", [])
        penalty_defaults = company_config.get("penalty_defaults", {
            "critical": 0,  # Critical handled separately
            "major": 10,
            "minor": 3
        })
        
        for violation in violations:
            severity = violation.get("severity", "minor")
            rule_id = violation.get("rule_id")
            
            if severity == "critical":
                # Critical violations handled in pass/fail logic
                penalty_breakdown.append({
                    "rule_id": rule_id,
                    "severity": severity,
                    "penalty_points": 0,
                    "reason": "Critical violation - handled separately"
                })
            else:
                penalty_points = penalty_defaults.get(severity, 0)
                total_penalties += penalty_points
                penalty_breakdown.append({
                    "rule_id": rule_id,
                    "severity": severity,
                    "penalty_points": penalty_points,
                    "reason": violation.get("description", f"{severity} violation")
                })
        
        return total_penalties, penalty_breakdown
    
    def _calculate_overall_score(
        self,
        stage_scores: List[Dict[str, Any]],
        total_penalties: float
    ) -> float:
        """
        Calculate overall score as weighted average of stage scores, then apply penalties.
        
        Overall score = (weighted average of stage scores) - penalties
        Where weighted average = sum(stage_score * stage_weight) / sum(stage_weights)
        """
        if not stage_scores:
            return 0.0
        
        # Calculate weighted average of stage scores
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for stage in stage_scores:
            stage_score = stage.get("score", 0.0)  # Already a percentage 0-100
            stage_weight = stage.get("weight", 0.0)
            
            total_weighted_score += stage_score * stage_weight
            total_weight += stage_weight
        
        # Calculate weighted average
        if total_weight > 0:
            weighted_avg_score = total_weighted_score / total_weight
        else:
            weighted_avg_score = 0.0
        
        # Apply penalties (penalties are point deductions, not percentages)
        overall_score = weighted_avg_score - total_penalties
        
        logger.debug(f"SCORING_OVERALL: weighted_avg={weighted_avg_score:.1f}, penalties={total_penalties:.1f}, final={overall_score:.1f}")
        
        return max(0.0, min(100.0, overall_score))
    
    def _determine_pass_fail(
        self,
        overall_score: float,
        stage_scores: List[Dict[str, Any]],
        policy_rule_results: Optional[Dict[str, Any]],
        company_config: Dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """Determine pass/fail status"""
        # Check for critical violations
        if policy_rule_results:
            violations = policy_rule_results.get("violations", [])
            critical_violations = [v for v in violations if v.get("severity") == "critical" and v.get("action") == "fail_overall"]
            if critical_violations:
                return False, "critical_violation"
        
        # Check overall threshold
        overall_threshold = company_config.get("overall_pass_threshold", 70)
        if overall_score < overall_threshold:
            return False, "below_threshold"
        
        # Check stage thresholds
        stage_threshold_enforced = company_config.get("stage_threshold_enforced", False)
        if stage_threshold_enforced:
            for stage in stage_scores:
                stage_threshold = stage.get("threshold", 0)
                if stage.get("score", 0) < stage_threshold:
                    return False, f"stage_below_threshold:{stage.get('stage_name')}"
        
        return True, None
    
    def _requires_human_review(
        self,
        stage_scores: List[Dict[str, Any]],
        policy_rule_results: Optional[Dict[str, Any]],
        company_config: Dict[str, Any]
    ) -> bool:
        """Determine if human review is required"""
        # Check for critical violations
        if policy_rule_results:
            violations = policy_rule_results.get("violations", [])
            if any(v.get("severity") == "critical" for v in violations):
                return True
        
        # Check confidence threshold
        confidence_threshold = company_config.get("human_review_confidence_threshold", 0.5)
        for stage in stage_scores:
            if stage.get("confidence", 1.0) < confidence_threshold:
                return True
        
        # Check overall confidence
        overall_confidence = self._calculate_overall_confidence(stage_scores)
        if overall_confidence < confidence_threshold:
            return True
        
        return False
    
    def _calculate_overall_confidence(
        self,
        stage_scores: List[Dict[str, Any]]
    ) -> float:
        """Calculate weighted overall confidence"""
        if not stage_scores:
            return 0.5
        
        total_weight = sum(s.get("weight", 0) for s in stage_scores)
        if total_weight == 0:
            return mean([s.get("confidence", 0.5) for s in stage_scores])
        
        weighted_sum = sum(s.get("confidence", 0.5) * s.get("weight", 0) for s in stage_scores)
        return weighted_sum / total_weight if total_weight > 0 else 0.5

