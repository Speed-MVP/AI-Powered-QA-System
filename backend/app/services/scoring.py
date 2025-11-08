from typing import Dict, List, Any
from decimal import Decimal
from app.models.evaluation_criteria import EvaluationCriteria
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


class ScoringService:
    def __init__(self):
        pass
    
    def calculate_scores(self, evaluation_data: Dict[str, Any], criteria: List[EvaluationCriteria]) -> Dict[str, Any]:
        """Calculate final scores from LLM evaluation data"""
        category_scores_data = evaluation_data.get("category_scores", {})
        
        # Create a set of valid category names (case-insensitive for matching)
        valid_categories = {c.category_name: c for c in criteria}
        valid_category_names_lower = {name.lower(): name for name in valid_categories.keys()}
        
        # Filter out any categories from LLM that don't exist in database
        filtered_category_scores = {}
        for llm_category, score_data in category_scores_data.items():
            # Try exact match first
            if llm_category in valid_categories:
                filtered_category_scores[llm_category] = score_data
            # Try case-insensitive match
            elif llm_category.lower() in valid_category_names_lower:
                actual_category_name = valid_category_names_lower[llm_category.lower()]
                filtered_category_scores[actual_category_name] = score_data
                logger.warning(f"Category name case mismatch: '{llm_category}' mapped to '{actual_category_name}'")
            else:
                logger.warning(f"Ignoring invalid category from LLM: '{llm_category}'. Valid categories: {list(valid_categories.keys())}")
        
        # Calculate weighted overall score
        total_weighted_score = Decimal("0.0")
        total_weight = Decimal("0.0")
        
        category_scores = []
        
        for criterion in criteria:
            category_name = criterion.category_name
            weight = Decimal(str(criterion.weight))
            
            # Use filtered scores (prioritize exact match, then case-insensitive)
            if category_name in filtered_category_scores:
                score_data = filtered_category_scores[category_name]
                score = int(score_data.get("score", 0))
                feedback = score_data.get("feedback", "")
            else:
                # Default if category not in LLM response (shouldn't happen with strict prompt, but handle it)
                score = 0
                feedback = "Category not evaluated by LLM"
                logger.warning(f"Category '{category_name}' not found in LLM response. Available: {list(filtered_category_scores.keys())}")
            
            category_scores.append({
                "category_name": category_name,
                "score": score,
                "feedback": feedback,
                "weight": float(weight),
                "passing_score": criterion.passing_score
            })
            
            # Calculate weighted score
            total_weighted_score += Decimal(str(score)) * weight / Decimal("100.0")
            total_weight += weight
        
        # Calculate overall score
        if total_weight > 0:
            overall_score = float(total_weighted_score / total_weight * Decimal("100.0"))
        else:
            overall_score = 0.0
        
        overall_score = int(round(overall_score))
        
        # Get resolution detection
        resolution_detected = evaluation_data.get("resolution_detected", False)
        resolution_confidence = float(evaluation_data.get("resolution_confidence", 0.0))
        
        # Get violations and filter to only include valid categories
        violations = evaluation_data.get("violations", [])
        filtered_violations = []
        
        for violation in violations:
            violation_category = violation.get("category_name") or violation.get("type", "")
            
            # Check if violation category matches a valid category
            is_valid = False
            if violation_category in valid_categories:
                is_valid = True
                # Update violation to use exact category name
                violation["category_name"] = violation_category
            elif violation_category.lower() in valid_category_names_lower:
                is_valid = True
                # Update violation to use exact category name from database
                violation["category_name"] = valid_category_names_lower[violation_category.lower()]
                logger.warning(f"Violation category name case mismatch: '{violation_category}' mapped to '{violation['category_name']}'")
            else:
                logger.warning(f"Ignoring violation with invalid category: '{violation_category}'. Valid categories: {list(valid_categories.keys())}")
            
            if is_valid:
                filtered_violations.append(violation)
        
        logger.info(f"Filtered {len(filtered_violations)} valid violations out of {len(violations)} total")
        
        return {
            "overall_score": overall_score,
            "resolution_detected": resolution_detected,
            "resolution_confidence": resolution_confidence,
            "category_scores": {cs["category_name"]: cs for cs in category_scores},
            "violations": filtered_violations
        }

