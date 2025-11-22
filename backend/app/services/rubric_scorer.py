"""
Phase 6: Rubric Scoring Engine
Converts LLM stage evaluations into category scores and overall score per Phase 6 spec.
"""

from typing import Dict, List, Any, Optional
from app.models.rubric_template import RubricTemplate, RubricCategory, RubricMapping
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class RubricScorer:
    """
    Phase 6: Rubric Scoring Engine
    Aggregates stage scores into category scores and overall score.
    """
    
    def score(
        self,
        rubric_template: RubricTemplate,
        llm_stage_evaluations: Dict[str, Dict[str, Any]],
        deterministic_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate category scores and overall score per Phase 6 spec.
        Returns FinalEvaluation dict.
        """
        category_scores = []
        stage_scores = {}
        
        # Extract stage scores from LLM evaluations
        for stage_id, stage_eval in llm_stage_evaluations.items():
            stage_scores[stage_id] = {
                "score": stage_eval.get("stage_score", 0),
                "confidence": stage_eval.get("stage_confidence", 0.5),
                "critical_violation": stage_eval.get("critical_violation", False)
            }
        
        # Calculate category scores
        for category in rubric_template.categories:
            # Get mappings for this category
            mappings = category.mappings
            
            if not mappings:
                # No mappings - default score or skip
                logger.warning(f"Category {category.name} has no mappings")
                category_score = 0
            else:
                # Collect target scores
                target_scores = []
                total_weight = sum(float(m.contribution_weight) for m in mappings)
                
                for mapping in mappings:
                    target_id = mapping.target_id
                    target_score = 0
                    
                    if mapping.target_type == "stage":
                        # Use stage score
                        if target_id in stage_scores:
                            target_score = stage_scores[target_id]["score"]
                        else:
                            # Missing stage - score = 0 per Phase 6 spec
                            logger.warning(f"Stage {target_id} not found in LLM evaluations")
                            target_score = 0
                    
                    elif mapping.target_type == "step":
                        # Calculate step score from stage results
                        # Find which stage contains this step
                        target_score = self._get_step_score(
                            target_id,
                            llm_stage_evaluations,
                            deterministic_result
                        )
                    
                    # Normalize contribution weight
                    normalized_weight = float(mapping.contribution_weight) / total_weight if total_weight > 0 else 0
                    target_scores.append({
                        "score": target_score,
                        "weight": normalized_weight,
                        "required": mapping.required_flag
                    })
                
                # Calculate weighted average
                category_score = sum(t["score"] * t["weight"] for t in target_scores)
                
                # Check for required flag failures
                for target in target_scores:
                    if target["required"] and target["score"] < category.pass_threshold:
                        # Required target failed - may need special handling
                        pass
            
            # Round to nearest integer
            category_score = round(category_score)
            
            # Clamp to 0-100
            category_score = max(0, min(100, category_score))
            
            # Check if category passed
            passed = category_score >= category.pass_threshold
            
            category_scores.append({
                "category_id": category.id,
                "name": category.name,
                "weight": float(category.weight),
                "score": category_score,
                "passed": passed
            })
        
        # Calculate overall score (weighted sum)
        overall_score = sum(
            c["score"] * (c["weight"] / 100)
            for c in category_scores
        )
        overall_score = round(overall_score)
        overall_score = max(0, min(100, overall_score))
        
        # Determine overall pass/fail
        # Check for critical violations first
        critical_violations = deterministic_result.get("rule_evaluations", [])
        has_critical = any(
            r.get("severity") == "critical" and not r.get("passed")
            for r in critical_violations
        )
        
        if has_critical:
            overall_passed = False
        else:
            # Check if any category failed
            any_category_failed = any(not c["passed"] for c in category_scores)
            overall_passed = not any_category_failed
        
        # Check for low confidence
        requires_human_review = any(
            s.get("confidence", 1.0) < 0.5
            for s in stage_scores.values()
        )
        
        return {
            "overall_score": overall_score,
            "overall_passed": overall_passed,
            "category_scores": category_scores,
            "stage_scores": stage_scores,
            "requires_human_review": requires_human_review
        }
    
    def _get_step_score(
        self,
        step_id: str,
        llm_stage_evaluations: Dict[str, Dict[str, Any]],
        deterministic_result: Dict[str, Any]
    ) -> int:
        """Get score for a specific step"""
        # Look through LLM stage evaluations for step
        for stage_id, stage_eval in llm_stage_evaluations.items():
            step_evaluations = stage_eval.get("step_evaluations", [])
            for step_eval in step_evaluations:
                if step_eval.get("step_id") == step_id:
                    # Step passed = 100, failed = 0
                    return 100 if step_eval.get("passed", False) else 0
        
        # Not found in LLM - check deterministic results
        stage_results = deterministic_result.get("stage_results", {})
        for stage_id, results in stage_results.items():
            step_results = results.get("step_results", [])
            for step_result in step_results:
                if step_result.get("step_id") == step_id:
                    return 100 if step_result.get("passed", False) else 0
        
        # Not found - return 0
        return 0

