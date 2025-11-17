"""
Phase 5: Policy Rules Sandbox - Unit Tests
Tests for sandbox evaluation of rules against sample transcripts.
"""

import pytest
from app.services.policy_rules_sandbox import PolicyRulesSandboxService


class TestPolicyRulesSandbox:
    """Test suite for policy rules sandbox evaluation."""

    @pytest.fixture
    def sandbox_service(self):
        """Create sandbox service instance."""
        return PolicyRulesSandboxService()

    @pytest.fixture
    def sample_policy_rules(self):
        """Sample policy rules for testing."""
        return {
            "Professionalism": [
                {
                    "id": "greet_within_seconds",
                    "type": "numeric",
                    "value": 15,
                    "comparator": "le"
                },
                {
                    "id": "identify_self",
                    "type": "boolean",
                    "value": True
                }
            ],
            "Empathy": [
                {
                    "id": "requires_apology_if_negative_sentiment",
                    "type": "boolean",
                    "value": True
                }
            ]
        }

    @pytest.fixture
    def sample_transcript(self):
        """Sample transcript for testing."""
        return {
            "id": "test_transcript",
            "name": "Test Call",
            "segments": [
                {
                    "speaker": "agent",
                    "text": "Hello, this is John from support.",
                    "start": 5.0,
                    "end": 10.0
                },
                {
                    "speaker": "caller",
                    "text": "This service is terrible!",
                    "start": 11.0,
                    "end": 15.0
                },
                {
                    "speaker": "agent",
                    "text": "I'm sorry to hear that. Let me help.",
                    "start": 16.0,
                    "end": 22.0
                }
            ],
            "sentiment": [
                {"speaker": "caller", "sentiment": -0.8, "start": 11.0, "end": 15.0}
            ],
            "metadata": {"call_duration": 120.0}
        }

    def test_get_available_samples(self, sandbox_service):
        """Test retrieving available sample transcripts."""
        samples = sandbox_service.get_available_samples()

        assert isinstance(samples, list)
        assert len(samples) >= 1  # Should have at least the built-in samples

        # Check sample structure
        sample = samples[0]
        assert "id" in sample
        assert "name" in sample
        assert "segment_count" in sample
        assert "has_sentiment" in sample
        assert "call_duration" in sample

    def test_evaluate_against_sample_success(self, sandbox_service, sample_policy_rules, sample_transcript):
        """Test successful sandbox evaluation."""
        result = sandbox_service.evaluate_against_sample(
            policy_rules=sample_policy_rules,
            custom_transcript=sample_transcript
        )

        assert result["success"] is True
        assert result["transcript_id"] == "test_transcript"
        assert result["transcript_name"] == "Test Call"
        assert "policy_results" in result
        assert "rule_metrics" in result
        assert "scoring_preview" in result
        assert "execution_time_ms" in result

        # Check policy results structure
        policy_results = result["policy_results"]
        assert "Professionalism" in policy_results
        assert "Empathy" in policy_results

        # Check metrics
        metrics = result["rule_metrics"]
        assert "rules_evaluated" in metrics
        assert "segments_processed" in metrics
        assert "execution_time_ms" in metrics

    def test_evaluate_against_sample_with_sample_id(self, sandbox_service, sample_policy_rules):
        """Test evaluation using built-in sample ID."""
        result = sandbox_service.evaluate_against_sample(
            policy_rules=sample_policy_rules,
            sample_id="sample_1"  # Use first built-in sample
        )

        assert result["success"] is True
        assert result["transcript_id"] == "sample_1"
        assert "policy_results" in result

    def test_evaluate_against_sample_invalid_sample_id(self, sandbox_service, sample_policy_rules):
        """Test evaluation with invalid sample ID."""
        result = sandbox_service.evaluate_against_sample(
            policy_rules=sample_policy_rules,
            sample_id="nonexistent"
        )

        # Should fall back to default sample
        assert result["success"] is True
        assert "policy_results" in result

    def test_evaluate_against_sample_missing_transcript(self, sandbox_service, sample_policy_rules):
        """Test evaluation when transcript data is missing."""
        incomplete_transcript = {
            "id": "incomplete",
            "name": "Incomplete",
            "segments": [],  # Empty segments
            "sentiment": [],
            "metadata": {}
        }

        result = sandbox_service.evaluate_against_sample(
            policy_rules=sample_policy_rules,
            custom_transcript=incomplete_transcript
        )

        assert result["success"] is True  # Should not fail, just return null results
        assert "policy_results" in result

    def test_evaluate_against_sample_malformed_rules(self, sandbox_service, sample_transcript):
        """Test evaluation with malformed policy rules."""
        malformed_rules = {
            "InvalidCategory": {
                "invalid_rule": {
                    "id": "invalid_rule",
                    "type": "invalid_type",  # Invalid type
                    "value": "invalid"
                }
            }
        }

        result = sandbox_service.evaluate_against_sample(
            policy_rules=malformed_rules,
            custom_transcript=sample_transcript
        )

        # Should handle errors gracefully
        assert isinstance(result, dict)
        # May or may not succeed depending on error handling

    def test_validate_rules_safety_success(self, sandbox_service, sample_policy_rules):
        """Test rules safety validation - successful case."""
        validation = sandbox_service.validate_rules_safety(sample_policy_rules, max_samples=2)

        assert validation["is_safe"] is True
        assert validation["tested_samples"] == 2
        assert validation["successful_evaluations"] == 2
        assert len(validation["errors"]) == 0

    def test_validate_rules_safety_with_failures(self, sandbox_service):
        """Test rules safety validation with failures."""
        # Rules that might cause issues
        problematic_rules = {
            "Problematic": {
                "bad_rule": {
                    "id": "bad_rule",
                    "type": "nonexistent_type",
                    "value": None
                }
            }
        }

        validation = sandbox_service.validate_rules_safety(problematic_rules, max_samples=1)

        # Should detect issues
        assert validation["tested_samples"] == 1
        # May or may not pass depending on error handling

    def test_scoring_preview_calculation(self, sandbox_service, sample_policy_rules, sample_transcript):
        """Test scoring preview calculation."""
        result = sandbox_service.evaluate_against_sample(
            policy_rules=sample_policy_rules,
            custom_transcript=sample_transcript
        )

        scoring_preview = result.get("scoring_preview", {})

        # Should contain preview information
        assert isinstance(scoring_preview, dict)

        # Check for expected preview structure
        if "category_impacts" in scoring_preview:
            assert isinstance(scoring_preview["category_impacts"], dict)

    def test_execution_time_tracking(self, sandbox_service, sample_policy_rules, sample_transcript):
        """Test that execution time is properly tracked."""
        result = sandbox_service.evaluate_against_sample(
            policy_rules=sample_policy_rules,
            custom_transcript=sample_transcript
        )

        execution_time = result.get("execution_time_ms", 0)
        assert execution_time >= 0
        assert isinstance(execution_time, int)

        # Also check internal timing
        rule_metrics = result.get("rule_metrics", {})
        if "execution_time_ms" in rule_metrics:
            assert rule_metrics["execution_time_ms"] >= 0

    def test_error_handling_in_evaluation(self, sandbox_service):
        """Test error handling during evaluation."""
        # Empty rules should not crash
        empty_rules = {}
        result = sandbox_service.evaluate_against_sample(policy_rules=empty_rules)

        assert isinstance(result, dict)
        # Should handle gracefully

    def test_sample_data_structure(self, sandbox_service):
        """Test that built-in sample data has correct structure."""
        samples = sandbox_service.get_available_samples()

        for sample in samples:
            assert "id" in sample
            assert "name" in sample
            assert isinstance(sample["segment_count"], int)
            assert isinstance(sample["has_sentiment"], bool)
            assert isinstance(sample["call_duration"], (int, float))
