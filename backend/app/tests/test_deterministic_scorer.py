"""
Phase 4: Deterministic Scorer - Unit Tests
Tests for rubric mapping, penalty application, and score calculation.
"""

import pytest
from decimal import Decimal
from app.services.deterministic_scorer import DeterministicScorer


class TestDeterministicScorer:
    """Test suite for deterministic scoring service."""

    @pytest.fixture
    def scorer(self):
        """Create scorer instance."""
        return DeterministicScorer()

    @pytest.fixture
    def sample_criteria(self):
        """Sample evaluation criteria with rubric levels."""
        return [
            {
                "category_name": "Professionalism",
                "weight": 40,
                "rubric_levels": [
                    {"level_name": "Excellent", "min_score": 90, "max_score": 100},
                    {"level_name": "Good", "min_score": 70, "max_score": 89},
                    {"level_name": "Average", "min_score": 50, "max_score": 69},
                    {"level_name": "Poor", "min_score": 30, "max_score": 49},
                    {"level_name": "Unacceptable", "min_score": 0, "max_score": 29}
                ]
            },
            {
                "category_name": "Empathy",
                "weight": 30,
                "rubric_levels": [
                    {"level_name": "Excellent", "min_score": 90, "max_score": 100},
                    {"level_name": "Good", "min_score": 70, "max_score": 89},
                    {"level_name": "Average", "min_score": 50, "max_score": 69},
                    {"level_name": "Poor", "min_score": 30, "max_score": 49},
                    {"level_name": "Unacceptable", "min_score": 0, "max_score": 29}
                ]
            },
            {
                "category_name": "Resolution",
                "weight": 30,
                "rubric_levels": [
                    {"level_name": "Excellent", "min_score": 90, "max_score": 100},
                    {"level_name": "Good", "min_score": 70, "max_score": 89},
                    {"level_name": "Average", "min_score": 50, "max_score": 69},
                    {"level_name": "Poor", "min_score": 30, "max_score": 49},
                    {"level_name": "Unacceptable", "min_score": 0, "max_score": 29}
                ]
            }
        ]

    @pytest.fixture
    def sample_rubric_levels(self):
        """Sample rubric level assignments from LLM."""
        return {
            "Professionalism": "Good",
            "Empathy": "Average",
            "Resolution": "Excellent"
        }

    @pytest.fixture
    def sample_policy_results(self):
        """Sample rule evaluation results with penalties."""
        return {
            "Professionalism": {
                "greet_within_seconds": {"passed": False, "evidence": "too slow", "penalty": 15}
            },
            "Empathy": {
                "requires_apology_if_negative": {"passed": True, "evidence": "apology given"}
            },
            "Resolution": {
                "issue_resolved": {"passed": True, "evidence": "resolution confirmed"}
            }
        }

    def test_rubric_score_mapping_standard(self, scorer):
        """Test standard rubric level to score mapping."""
        # Test all standard levels
        assert scorer._get_rubric_score("Excellent", {}) == 95
        assert scorer._get_rubric_score("Good", {}) == 82
        assert scorer._get_rubric_score("Average", {}) == 67
        assert scorer._get_rubric_score("Poor", {}) == 50
        assert scorer._get_rubric_score("Unacceptable", {}) == 20

    def test_rubric_score_mapping_custom_ranges(self, scorer):
        """Test custom rubric range mapping."""
        custom_ranges = {
            "Excellent": {"min_score": 95, "max_score": 100},
            "Good": {"min_score": 80, "max_score": 94},
            "Average": {"min_score": 60, "max_score": 79}
        }

        assert scorer._get_rubric_score("Excellent", custom_ranges) == 97  # (95+100)/2
        assert scorer._get_rubric_score("Good", custom_ranges) == 87       # (80+94)/2
        assert scorer._get_rubric_score("Average", custom_ranges) == 69    # (60+79)/2

    def test_rubric_score_mapping_unknown_level(self, scorer):
        """Test unknown rubric level defaults to Average."""
        assert scorer._get_rubric_score("Unknown", {}) == 67

    def test_calculate_category_scores_with_penalties(self, scorer, sample_rubric_levels, sample_policy_results, sample_criteria):
        """Test category score calculation with penalties applied."""
        rubric_ranges = scorer.extract_rubric_ranges_from_criteria(sample_criteria)

        category_scores = scorer.calculate_category_scores(
            sample_rubric_levels,
            sample_policy_results,
            rubric_ranges
        )

        # Professionalism: Good (79) - penalty (15) = 64
        prof_score = category_scores["Professionalism"]
        assert prof_score["rubric_level"] == "Good"
        assert prof_score["base_score"] == 79
        assert len(prof_score["penalties_applied"]) == 1
        assert prof_score["penalties_applied"][0]["penalty"] == 15
        assert prof_score["final_score"] == 64

        # Empathy: Average (59) - no penalties = 59
        empathy_score = category_scores["Empathy"]
        assert empathy_score["rubric_level"] == "Average"
        assert empathy_score["base_score"] == 59
        assert len(empathy_score["penalties_applied"]) == 0
        assert empathy_score["final_score"] == 59

        # Resolution: Excellent (95) - no penalties = 95
        resolution_score = category_scores["Resolution"]
        assert resolution_score["rubric_level"] == "Excellent"
        assert resolution_score["base_score"] == 95
        assert len(resolution_score["penalties_applied"]) == 0
        assert resolution_score["final_score"] == 95

    def test_calculate_overall_score_weighted(self, scorer, sample_criteria):
        """Test weighted overall score calculation."""
        category_scores = {
            "Professionalism": {"final_score": 67},
            "Empathy": {"final_score": 67},
            "Resolution": {"final_score": 95}
        }

        category_weights = scorer.extract_category_weights(sample_criteria)

        overall_score = scorer.calculate_overall_score(category_scores, category_weights)

        # Expected: (67 * 0.4) + (67 * 0.3) + (95 * 0.3) = 26.8 + 20.1 + 28.5 = 75.4
        assert overall_score == Decimal('75.4')

    def test_penalty_application_multiple_penalties(self, scorer):
        """Test application of multiple penalties."""
        rubric_levels = {"TestCategory": "Good"}
        policy_results = {
            "TestCategory": {
                "rule1": {"passed": False, "penalty": 10},
                "rule2": {"passed": False, "penalty": 5},
                "rule3": {"passed": True}  # No penalty
            }
        }

        category_scores = scorer.calculate_category_scores(rubric_levels, policy_results, {})

        test_score = category_scores["TestCategory"]
        assert test_score["base_score"] == 82
        assert len(test_score["penalties_applied"]) == 2
        assert test_score["final_score"] == 67  # 82 - 10 - 5

    def test_penalty_application_score_clamping(self, scorer):
        """Test score clamping when penalties exceed base score."""
        rubric_levels = {"TestCategory": "Poor"}  # 50 points
        policy_results = {
            "TestCategory": {
                "major_violation": {"passed": False, "penalty": 60}  # Penalty > base score
            }
        }

        category_scores = scorer.calculate_category_scores(rubric_levels, policy_results, {})

        test_score = category_scores["TestCategory"]
        assert test_score["final_score"] == 0  # Clamped to minimum

    def test_penalty_application_score_clamping_maximum(self, scorer):
        """Test score clamping at maximum (though penalties shouldn't increase score)."""
        rubric_levels = {"TestCategory": "Excellent"}  # 95 points
        policy_results = {
            "TestCategory": {
                "negative_penalty": {"passed": False, "penalty": -10}  # Invalid negative penalty
            }
        }

        category_scores = scorer.calculate_category_scores(rubric_levels, policy_results, {})

        test_score = category_scores["TestCategory"]
        assert test_score["final_score"] == 95  # No change for invalid penalty

    def test_extract_rubric_ranges_from_criteria(self, scorer, sample_criteria):
        """Test extraction of rubric ranges from criteria."""
        rubric_ranges = scorer.extract_rubric_ranges_from_criteria(sample_criteria)

        assert "Professionalism" in rubric_ranges
        assert "Excellent" in rubric_ranges["Professionalism"]
        assert rubric_ranges["Professionalism"]["Excellent"]["min_score"] == 90
        assert rubric_ranges["Professionalism"]["Excellent"]["max_score"] == 100

        assert "Poor" in rubric_ranges["Professionalism"]
        assert rubric_ranges["Professionalism"]["Poor"]["min_score"] == 30
        assert rubric_ranges["Professionalism"]["Poor"]["max_score"] == 49

    def test_extract_category_weights(self, scorer, sample_criteria):
        """Test extraction of category weights."""
        weights = scorer.extract_category_weights(sample_criteria)

        assert weights["Professionalism"] == Decimal('40')
        assert weights["Empathy"] == Decimal('30')
        assert weights["Resolution"] == Decimal('30')

    def test_calculate_overall_score_zero_weights(self, scorer):
        """Test overall score calculation with zero weights."""
        category_scores = {"Test": {"final_score": 80}}
        category_weights = {}

        overall_score = scorer.calculate_overall_score(category_scores, category_weights)

        assert overall_score == Decimal('0')

    def test_calculate_overall_score_normalization(self, scorer):
        """Test that overall score is properly normalized to 0-100 range."""
        category_scores = {"Test": {"final_score": 50}}
        category_weights = {"Test": Decimal('100')}

        overall_score = scorer.calculate_overall_score(category_scores, category_weights)

        assert Decimal('0') <= overall_score <= Decimal('100')

    def test_penalty_calculation_no_penalties(self, scorer):
        """Test penalty calculation when no penalties exist."""
        penalties = scorer._calculate_category_penalties("Test", {"Test": {"rule1": {"passed": True}}})
        assert penalties == []

    def test_penalty_calculation_with_penalties(self, scorer):
        """Test penalty calculation with various penalty scenarios."""
        policy_results = {
            "Test": {
                "rule1": {"passed": False, "penalty": 10, "evidence": "violation"},
                "rule2": {"passed": False, "penalty": 5, "evidence": "another violation"},
                "rule3": {"passed": True}  # No penalty
            }
        }

        penalties = scorer._calculate_category_penalties("Test", policy_results)

        assert len(penalties) == 2
        assert penalties[0]["rule_id"] == "rule1"
        assert penalties[0]["penalty"] == 10
        assert penalties[1]["rule_id"] == "rule2"
        assert penalties[1]["penalty"] == 5
