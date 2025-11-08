from typing import List
from decimal import Decimal


def validate_weight_sum(weights: List[Decimal], expected_sum: Decimal = Decimal("100.00")) -> bool:
    """Validate that weights sum to expected_sum (default 100.00)"""
    total = sum(weights)
    return abs(total - expected_sum) < Decimal("0.01")  # Allow small floating point differences


def validate_score_range(score: int, min_score: int = 0, max_score: int = 100) -> bool:
    """Validate that score is within range"""
    return min_score <= score <= max_score

