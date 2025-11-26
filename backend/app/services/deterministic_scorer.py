"""
Phase 4: Deterministic Scorer
Converts rubric levels to numeric scores with penalty application.
"""

import logging
from typing import Dict, Any, List, Tuple
from decimal import Decimal, ROUND_HALF_UP

logger = logging.getLogger(__name__)


class DeterministicScorer:
    """
    Converts rubric levels to numeric scores using deterministic formulas.

    Handles:
    - Rubric level to numeric score mapping
    - Rule penalty application
    - Score clamping and validation
    - Weighted overall score calculation
    """

    # Standard rubric level mappings (midpoints of ranges)
    RUBRIC_LEVEL_SCORES = {
        "Excellent": 95,    # midpoint of 90-100
        "Good": 82,         # midpoint of 70-89
        "Average": 67,      # midpoint of 50-69
        "Poor": 50,         # midpoint of 30-49
        "Unacceptable": 20  # midpoint of 0-29
    }

    def __init__(self):
        pass

    def calculate_category_scores(
        self,
        rubric_levels: Dict[str, str],
        policy_results: Dict[str, Any],
        rubric_ranges: Dict[str, Dict[str, Dict[str, int]]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculate numeric scores for each category with penalties applied.

        Args:
            rubric_levels: category -> rubric_level mapping from LLM
            policy_results: Rule engine evaluation results
            rubric_ranges: Actual rubric ranges from database (for custom mappings)

        Returns:
            Dict mapping category to score details
        """
        category_scores = {}

        for category, level in rubric_levels.items():
            # Get base score from rubric level
            base_score = self._get_rubric_score(level, rubric_ranges.get(category, {}))

            # Calculate penalties for this category
            penalties = self._calculate_category_penalties(category, policy_results)

            # Apply penalties
            final_score = self._apply_penalties(base_score, penalties)

            category_scores[category] = {
                "rubric_level": level,
                "base_score": base_score,
                "penalties_applied": penalties,
                "final_score": final_score
            }

        return category_scores

    def calculate_overall_score(
        self,
        category_scores: Dict[str, Dict[str, Any]],
        category_weights: Dict[str, Decimal]
    ) -> Decimal:
        """
        Calculate weighted overall score from category scores.

        Args:
            category_scores: Category score details
            category_weights: category -> weight mapping (as Decimal percentages)

        Returns:
            Weighted overall score (0-100)
        """
        total_weighted_score = Decimal('0')
        total_weight = Decimal('0')

        for category, score_data in category_scores.items():
            if category in category_weights:
                weight = category_weights[category]
                score = Decimal(str(score_data["final_score"]))

                total_weighted_score += score * (weight / Decimal('100'))
                total_weight += weight

        if total_weight == 0:
            logger.warning("No valid category weights found, returning 0")
            return Decimal('0')

        # Round to 2 decimal places
        overall_score = total_weighted_score.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # Clamp to valid range
        overall_score = max(Decimal('0'), min(Decimal('100'), overall_score))

        return overall_score

    def _get_rubric_score(self, level: str, custom_ranges: Dict[str, Dict[str, int]]) -> int:
        """
        Get numeric score for a rubric level.

        Args:
            level: Rubric level name
            custom_ranges: Custom rubric ranges for this category (optional)

        Returns:
            Numeric score
        """
        # Use custom ranges if provided
        if custom_ranges and level in custom_ranges:
            range_data = custom_ranges[level]
            min_score = range_data.get("min_score", 0)
            max_score = range_data.get("max_score", 100)
            # Return midpoint
            return (min_score + max_score) // 2

        # Use standard mapping
        return self.RUBRIC_LEVEL_SCORES.get(level, 67)  # Default to Average

    def _calculate_category_penalties(self, category: str, policy_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Calculate penalties for a category based on rule failures.

        Args:
            category: Category name
            policy_results: Rule evaluation results

        Returns:
            List of penalty details
        """
        penalties = []

        if category not in policy_results:
            return penalties

        category_results = policy_results[category]

        for rule_id, rule_result in category_results.items():
            # Extract penalty from rule result (if present)
            penalty = rule_result.get("penalty", 0)
            if penalty > 0:
                penalties.append({
                    "rule_id": rule_id,
                    "penalty": penalty,
                    "reason": rule_result.get("evidence", "Rule violation")
                })

        return penalties

    def _apply_penalties(self, base_score: int, penalties: List[Dict[str, Any]]) -> int:
        """
        Apply penalties to base score with clamping.

        Args:
            base_score: Base rubric score
            penalties: List of penalties to apply

        Returns:
            Final score after penalties (0-100)
        """
        total_penalty = sum(penalty["penalty"] for penalty in penalties)
        final_score = base_score - total_penalty

        # Clamp to valid range
        final_score = max(0, min(100, final_score))

        return final_score

    def extract_rubric_ranges_from_criteria(self, criteria: List[Dict[str, Any]]) -> Dict[str, Dict[str, Dict[str, int]]]:
        """
        Extract rubric ranges from evaluation criteria for custom scoring.

        Args:
            criteria: List of evaluation criteria with rubric levels

        Returns:
            category -> level -> {min_score, max_score} mapping
        """
        rubric_ranges = {}

        for criterion in criteria:
            category_name = criterion["category_name"]
            rubric_ranges[category_name] = {}

            for level in criterion.get("rubric_levels", []):
                level_name = level["level_name"]
                rubric_ranges[category_name][level_name] = {
                    "min_score": level["min_score"],
                    "max_score": level["max_score"]
                }

        return rubric_ranges

    def extract_category_weights(self, criteria: List[Dict[str, Any]]) -> Dict[str, Decimal]:
        """
        Extract category weights from evaluation criteria.

        Args:
            criteria: List of evaluation criteria

        Returns:
            category -> weight mapping
        """
        weights = {}
        for criterion in criteria:
            weights[criterion["category_name"]] = Decimal(str(criterion["weight"]))

        return weights








