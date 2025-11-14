from typing import Dict, List, Any, Optional
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

    def calculate_ensemble_scores(
        self,
        llm_scores: Dict[str, Any],
        rule_scores: Optional[Dict[str, Any]] = None,
        emotion_deviation_scores: Optional[Dict[str, Any]] = None,
        criteria: List[EvaluationCriteria] = None
    ) -> Dict[str, Any]:
        """
        Phase 2: Calculate ensemble scores combining LLM, rule engine, and emotion analysis.
        Weighted fusion: final_score = (llm*0.5 + rule*0.3 + emotion*0.2)
        """
        ensemble_category_scores = {}
        ensemble_violations = []

        # Get all unique categories from all sources
        all_categories = set()
        if llm_scores.get("category_scores"):
            all_categories.update(llm_scores["category_scores"].keys())
        if rule_scores:
            all_categories.update(rule_scores.keys())
        if emotion_deviation_scores:
            all_categories.update(emotion_deviation_scores.keys())

        # Calculate ensemble scores for each category
        for category in all_categories:
            llm_score = None
            rule_score = None
            emotion_score = None

            # Get individual scores
            if llm_scores.get("category_scores", {}).get(category):
                llm_score = llm_scores["category_scores"][category].get("score", 0)

            if rule_scores and rule_scores.get(category):
                rule_score = rule_scores[category].get("score", 0)

            if emotion_deviation_scores and emotion_deviation_scores.get(category):
                emotion_score = emotion_deviation_scores[category].get("score", 0)

            # Calculate weighted ensemble score
            weights = {"llm": 0.5, "rule": 0.3, "emotion": 0.2}
            weighted_sum = 0.0
            total_weight = 0.0

            ensemble_components = []

            if llm_score is not None:
                weighted_sum += llm_score * weights["llm"]
                total_weight += weights["llm"]
                ensemble_components.append(f"LLM:{llm_score}")

            if rule_score is not None:
                weighted_sum += rule_score * weights["rule"]
                total_weight += weights["rule"]
                ensemble_components.append(f"Rule:{rule_score}")

            if emotion_score is not None:
                weighted_sum += emotion_score * weights["emotion"]
                total_weight += weights["emotion"]
                ensemble_components.append(f"Emotion:{emotion_score}")

            # Calculate final ensemble score
            if total_weight > 0:
                ensemble_score = int(round(weighted_sum / total_weight))
            else:
                ensemble_score = 0

            # Create ensemble feedback
            ensemble_feedback = f"Ensemble Score: {ensemble_score} ("
            ensemble_feedback += " + ".join(ensemble_components)
            ensemble_feedback += ")"

            # Add confidence indicator
            if total_weight >= 0.8:  # At least 2 components
                ensemble_feedback += " - High confidence ensemble"
            elif total_weight >= 0.5:  # At least 1 component
                ensemble_feedback += " - Medium confidence ensemble"
            else:
                ensemble_feedback += " - Low confidence ensemble"

            ensemble_category_scores[category] = {
                "score": ensemble_score,
                "feedback": ensemble_feedback,
                "ensemble_components": {
                    "llm_score": llm_score,
                    "rule_score": rule_score,
                    "emotion_score": emotion_score,
                    "weights": weights,
                    "total_weight": total_weight
                }
            }

        # Combine violations from all sources
        if llm_scores.get("violations"):
            ensemble_violations.extend(llm_scores["violations"])

        if rule_scores:
            for category, category_data in rule_scores.items():
                if category_data.get("violations"):
                    ensemble_violations.extend(category_data["violations"])

        if emotion_deviation_scores:
            for category, category_data in emotion_deviation_scores.items():
                if category_data.get("violations"):
                    ensemble_violations.extend(category_data["violations"])

        # Calculate overall ensemble score using category weights
        total_weighted_score = Decimal("0.0")
        total_weight = Decimal("0.0")

        ensemble_category_list = []

        if criteria:
            for criterion in criteria:
                category_name = criterion.category_name
                weight = Decimal(str(criterion.weight))

                if category_name in ensemble_category_scores:
                    score = ensemble_category_scores[category_name]["score"]
                    ensemble_category_list.append({
                        "category_name": category_name,
                        "score": score,
                        "feedback": ensemble_category_scores[category_name]["feedback"],
                        "weight": float(weight),
                        "passing_score": criterion.passing_score,
                        "ensemble_components": ensemble_category_scores[category_name]["ensemble_components"]
                    })

                    total_weighted_score += Decimal(str(score)) * weight / Decimal("100.0")
                    total_weight += weight

        # Calculate overall score
        if total_weight > 0:
            overall_score = float(total_weighted_score / total_weight * Decimal("100.0"))
        else:
            overall_score = 0.0

        overall_score = int(round(overall_score))

        logger.info(f"Ensemble evaluation completed: {overall_score} overall score, "
                   f"{len(ensemble_category_scores)} categories, {len(ensemble_violations)} violations")

        return {
            "overall_score": overall_score,
            "resolution_detected": llm_scores.get("resolution_detected", False),
            "resolution_confidence": llm_scores.get("resolution_confidence", 0.0),
            "category_scores": {cs["category_name"]: cs for cs in ensemble_category_list} if ensemble_category_list else ensemble_category_scores,
            "violations": ensemble_violations,
            "ensemble_method": "weighted_fusion",
            "ensemble_weights": weights,
            "evaluation_sources": {
                "llm_available": bool(llm_scores.get("category_scores")),
                "rules_available": bool(rule_scores),
                "emotion_available": bool(emotion_deviation_scores)
            }
        }

