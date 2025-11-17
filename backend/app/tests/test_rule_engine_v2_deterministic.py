"""
Phase 3: Rule Engine V2 - Unit Tests for Deterministic Rule Evaluation
Tests for zero-randomness, objective rule enforcement.
"""

import pytest
from app.services.rule_engine_v2_deterministic import RuleEngineV2Deterministic


class TestRuleEngineV2Deterministic:
    """Comprehensive tests for deterministic rule engine."""

    @pytest.fixture
    def rule_engine(self):
        """Create Rule Engine V2 instance."""
        return RuleEngineV2Deterministic()

    @pytest.fixture
    def sample_transcript_segments(self):
        """Sample transcript for testing."""
        return [
            {
                "speaker": "agent",
                "text": "Hello, thank you for calling Tech Support. This is Sarah speaking.",
                "start": 5.0,
                "end": 12.0
            },
            {
                "speaker": "caller",
                "text": "Hi, I'm having issues with my account.",
                "start": 13.0,
                "end": 18.0
            },
            {
                "speaker": "agent",
                "text": "I'm sorry to hear that. Can you verify your account number?",
                "start": 19.0,
                "end": 25.0
            },
            {
                "speaker": "caller",
                "text": "I'm really frustrated with this service!",
                "start": 26.0,
                "end": 30.0
            },
            {
                "speaker": "agent",
                "text": "I apologize for the inconvenience. Let me help you right away.",
                "start": 31.0,
                "end": 37.0
            }
        ]

    @pytest.fixture
    def sample_sentiment(self):
        """Sample sentiment analysis data."""
        return [
            {"speaker": "caller", "sentiment": -0.6, "start": 26.0, "end": 30.0},  # Negative
            {"speaker": "agent", "sentiment": 0.2, "start": 31.0, "end": 37.0}     # Positive
        ]

    @pytest.fixture
    def sample_policy_rules(self):
        """Sample policy rules for testing."""
        return {
            "Professionalism": [
                {"id": "greet_within_seconds", "type": "numeric", "value": 15, "comparator": "le"},
                {"id": "identify_self", "type": "boolean", "value": True}
            ],
            "Empathy": [
                {"id": "requires_apology_if_negative_sentiment", "type": "boolean", "value": True}
            ],
            "Compliance": [
                {"id": "required_disclosures", "type": "list", "items": ["recording_notice", "privacy"]}
            ]
        }

    def test_evaluate_recording_complete_flow(self, rule_engine, sample_policy_rules, sample_transcript_segments, sample_sentiment):
        """Test complete evaluation flow with all rule types."""
        results, metrics = rule_engine.evaluate_recording(
            policy_rules=sample_policy_rules,
            transcript_segments=sample_transcript_segments,
            sentiment_analysis=sample_sentiment,
            metadata={"call_duration": 120.0}
        )

        # Verify structure
        assert "Professionalism" in results
        assert "Empathy" in results
        assert "Compliance" in results

        # Verify numeric rule
        greet_result = results["Professionalism"]["greet_within_seconds"]
        assert greet_result["passed"] is True  # 5.0 <= 15.0
        assert greet_result["actual_value"] == 5.0
        assert greet_result["required_value"] == 15

        # Verify boolean rules
        assert results["Professionalism"]["identify_self"]["passed"] is True
        assert results["Empathy"]["requires_apology_if_negative_sentiment"]["passed"] is True

        # Verify metrics
        assert metrics["rules_evaluated"] == 4  # greet, identify, apology, disclosures
        assert metrics["segments_processed"] == 5
        assert "execution_time_ms" in metrics
        assert metrics["execution_time_ms"] >= 0

    def test_boolean_identify_self_pass(self, rule_engine, sample_transcript_segments):
        """Test identify_self boolean rule - pass case."""
        rule = {"id": "identify_self", "type": "boolean", "value": True}

        result = rule_engine._evaluate_boolean_rule(rule, sample_transcript_segments, None, {})

        assert result.rule_id == "identify_self"
        assert result.passed is True
        assert "found identification keyword" in result.evidence

    def test_boolean_identify_self_fail(self, rule_engine):
        """Test identify_self boolean rule - fail case."""
        segments_no_intro = [
            {"speaker": "caller", "text": "Hello?", "start": 0.0, "end": 2.0},
            {"speaker": "agent", "text": "How can I help you?", "start": 3.0, "end": 8.0}
        ]

        rule = {"id": "identify_self", "type": "boolean", "value": True}

        result = rule_engine._evaluate_boolean_rule(rule, segments_no_intro, None, {})

        assert result.passed is False
        assert "no identification keywords found" in result.evidence

    def test_boolean_apology_negative_sentiment_pass(self, rule_engine, sample_transcript_segments, sample_sentiment):
        """Test apology rule - pass case (apology found after negative sentiment)."""
        rule = {"id": "requires_apology_if_negative_sentiment", "type": "boolean", "value": True}

        result = rule_engine._evaluate_boolean_rule(rule, sample_transcript_segments, sample_sentiment, {})

        assert result.passed is True
        assert "apology found after" in result.evidence

    def test_boolean_apology_negative_sentiment_fail(self, rule_engine, sample_sentiment):
        """Test apology rule - fail case (no apology after negative sentiment)."""
        segments_no_apology = [
            {"speaker": "caller", "text": "This is terrible!", "start": 10.0, "end": 15.0},
            {"speaker": "agent", "text": "Let me check that for you.", "start": 16.0, "end": 20.0}  # No apology
        ]

        rule = {"id": "requires_apology_if_negative_sentiment", "type": "boolean", "value": True}

        result = rule_engine._evaluate_boolean_rule(rule, segments_no_apology, sample_sentiment, {})

        assert result.passed is False
        assert "no apology found after negative sentiment" in result.evidence

    def test_boolean_apology_no_sentiment_data(self, rule_engine, sample_transcript_segments):
        """Test apology rule when no sentiment data is available."""
        rule = {"id": "requires_apology_if_negative_sentiment", "type": "boolean", "value": True}

        result = rule_engine._evaluate_boolean_rule(rule, sample_transcript_segments, None, {})

        assert result.passed is None  # None indicates no sentiment data
        assert "no sentiment data available" in result.evidence

    def test_numeric_greet_within_seconds_pass(self, rule_engine, sample_transcript_segments):
        """Test greet_within_seconds - pass case."""
        rule = {"id": "greet_within_seconds", "type": "numeric", "value": 10, "comparator": "le"}

        result = rule_engine._evaluate_numeric_rule(rule, sample_transcript_segments, None, {})

        assert result.passed is True
        assert result.actual_value == 5.0
        assert result.required_value == 10
        assert "first agent utterance at 5.0s" in result.evidence

    def test_numeric_greet_within_seconds_fail(self, rule_engine):
        """Test greet_within_seconds - fail case."""
        late_segments = [
            {"speaker": "agent", "text": "Hello!", "start": 25.0, "end": 27.0}  # Late greeting
        ]

        rule = {"id": "greet_within_seconds", "type": "numeric", "value": 10, "comparator": "le"}

        result = rule_engine._evaluate_numeric_rule(rule, late_segments, None, {})

        assert result.passed is False
        assert result.actual_value == 25.0
        assert result.required_value == 10

    def test_numeric_call_duration(self, rule_engine):
        """Test call duration numeric rule."""
        rule = {"id": "call_duration_max", "type": "numeric", "value": 300, "comparator": "le"}
        metadata = {"call_duration": 180.0}

        result = rule_engine._evaluate_numeric_rule(rule, [], None, metadata)

        assert result.passed is True
        assert result.actual_value == 180.0
        assert result.required_value == 300

    def test_numeric_max_agent_silence(self, rule_engine):
        """Test maximum agent silence calculation."""
        segments_with_silence = [
            {"speaker": "agent", "text": "Hello", "start": 0.0, "end": 2.0},
            {"speaker": "caller", "text": "Hi", "start": 3.0, "end": 5.0},
            {"speaker": "agent", "text": "How can I help?", "start": 10.0, "end": 12.0}  # 5s silence
        ]

        rule = {"id": "agent_silence_max", "type": "numeric", "value": 3.0, "comparator": "le"}

        result = rule_engine._evaluate_numeric_rule(rule, segments_with_silence, None, {})

        assert result.passed is False  # 8.0 > 3.0
        assert result.actual_value == 8.0
        assert result.required_value == 3.0

    def test_list_required_disclosures_pass(self, rule_engine):
        """Test required disclosures - pass case."""
        segments_with_disclosures = [
            {"speaker": "agent", "text": "This call is recorded for quality assurance. We respect your privacy and personal information.", "start": 0.0, "end": 5.0}
        ]

        rule = {"id": "required_disclosures", "type": "list", "items": ["recording_notice", "privacy"]}

        result = rule_engine._evaluate_list_rule(rule, segments_with_disclosures, None, {})

        assert result.passed["missing"] == []
        assert len(result.passed["present"]) == 2
        assert "recording_notice" in result.passed["present"]
        assert "privacy" in result.passed["present"]

    def test_list_required_disclosures_partial(self, rule_engine):
        """Test required disclosures - partial completion."""
        segments_partial = [
            {"speaker": "agent", "text": "This call is recorded for training.", "start": 0.0, "end": 5.0}
        ]

        rule = {"id": "required_disclosures", "type": "list", "items": ["recording_notice", "privacy"]}

        result = rule_engine._evaluate_list_rule(rule, segments_partial, None, {})

        assert result.passed["missing"] == ["privacy"]
        assert result.passed["present"] == ["recording_notice"]

    def test_evaluate_with_missing_transcript(self, rule_engine, sample_policy_rules):
        """Test evaluation when transcript is missing."""
        results, metrics = rule_engine.evaluate_recording(
            policy_rules=sample_policy_rules,
            transcript_segments=[],
            sentiment_analysis=None,
            metadata={}
        )

        # All rules should be marked as null
        for category, rules in results.items():
            for rule_id, rule_result in rules.items():
                assert rule_result["passed"] is None
                assert rule_result["error"] == "transcript not available"

        assert metrics["segments_processed"] == 0
        assert metrics["errors"] == 4  # All rules failed due to missing transcript

    def test_malformed_rule_handling(self, rule_engine):
        """Test handling of malformed rules."""
        malformed_policy_rules = {
            "Test": [
                {"type": "boolean", "value": True},  # Missing id
                {"id": "bad_type", "type": "invalid", "value": True},  # Invalid type
                {"id": "incomplete", "type": "numeric"}  # Missing value
            ]
        }

        results, metrics = rule_engine.evaluate_recording(
            policy_rules=malformed_policy_rules,
            transcript_segments=[{"speaker": "agent", "text": "test", "start": 0.0, "end": 1.0}],
            sentiment_analysis=None,
            metadata={}
        )

        assert metrics["errors"] >= 2  # At least malformed and missing value rules should error
        assert all(rule_result["passed"] is None for category_results in results.values()
                  for rule_result in category_results.values())

    def test_empty_policy_rules(self, rule_engine):
        """Test evaluation with empty policy rules."""
        results, metrics = rule_engine.evaluate_recording(
            policy_rules={},
            transcript_segments=[],
            sentiment_analysis=None,
            metadata={}
        )

        assert results == {"error": "No valid policy rules provided"}
        assert metrics["rules_evaluated"] == 0
        assert metrics["categories_evaluated"] == 0

    def test_numeric_comparators(self, rule_engine):
        """Test all numeric comparators work correctly."""
        test_cases = [
            ("le", 10, 15, True),
            ("le", 20, 15, False),
            ("lt", 10, 15, True),
            ("lt", 15, 15, False),
            ("ge", 20, 15, True),
            ("ge", 10, 15, False),
            ("gt", 20, 15, True),
            ("gt", 10, 15, False),
            ("eq", 15, 15, True),
            ("eq", 10, 15, False),
        ]

        for comparator, actual, required, expected in test_cases:
            assert rule_engine._compare_numeric(actual, comparator, required) == expected

    def test_performance_under_50ms(self, rule_engine, sample_policy_rules, sample_transcript_segments, sample_sentiment):
        """Test that evaluation completes under 50ms performance requirement."""
        import time

        start_time = time.time()
        results, metrics = rule_engine.evaluate_recording(
            policy_rules=sample_policy_rules,
            transcript_segments=sample_transcript_segments,
            sentiment_analysis=sample_sentiment,
            metadata={"call_duration": 120.0}
        )
        end_time = time.time()

        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds

        assert execution_time < 50.0, f"Evaluation took {execution_time}ms, exceeds 50ms limit"
        assert metrics["execution_time_ms"] < 50.0

    def test_deterministic_results(self, rule_engine, sample_policy_rules, sample_transcript_segments, sample_sentiment):
        """Test that results are deterministic - same input produces same output."""
        # Run evaluation multiple times
        results1, _ = rule_engine.evaluate_recording(
            policy_rules=sample_policy_rules,
            transcript_segments=sample_transcript_segments,
            sentiment_analysis=sample_sentiment,
            metadata={"call_duration": 120.0}
        )

        results2, _ = rule_engine.evaluate_recording(
            policy_rules=sample_policy_rules,
            transcript_segments=sample_transcript_segments,
            sentiment_analysis=sample_sentiment,
            metadata={"call_duration": 120.0}
        )

        assert results1 == results2

    def test_complex_scenario_integration(self, rule_engine):
        """Test a complex real-world scenario with multiple rule types."""
        # Complex transcript with multiple scenarios
        complex_transcript = [
            {"speaker": "agent", "text": "Hello, this is John from customer service.", "start": 2.0, "end": 6.0},
            {"speaker": "caller", "text": "This service is awful!", "start": 7.0, "end": 10.0},
            {"speaker": "agent", "text": "I'm sorry you're experiencing issues. Can you verify your account?", "start": 11.0, "end": 16.0},
            {"speaker": "caller", "text": "Yes, account 12345", "start": 17.0, "end": 20.0},
            {"speaker": "agent", "text": "This call may be recorded for quality purposes.", "start": 21.0, "end": 25.0},
        ]

        complex_sentiment = [
            {"speaker": "caller", "sentiment": -0.8, "start": 7.0, "end": 10.0},  # Very negative
        ]

        complex_rules = {
            "Professionalism": [
                {"id": "greet_within_seconds", "type": "numeric", "value": 5, "comparator": "le"},
                {"id": "identify_self", "type": "boolean", "value": True}
            ],
            "Empathy": [
                {"id": "requires_apology_if_negative_sentiment", "type": "boolean", "value": True}
            ],
            "Compliance": [
                {"id": "requires_account_verification", "type": "boolean", "value": True},
                {"id": "required_disclosures", "type": "list", "items": ["recording_notice"]}
            ]
        }

        results, metrics = rule_engine.evaluate_recording(
            policy_rules=complex_rules,
            transcript_segments=complex_transcript,
            sentiment_analysis=complex_sentiment,
            metadata={}
        )

        # Verify all rules pass in this well-handled scenario
        assert results["Professionalism"]["greet_within_seconds"]["passed"] is True  # 2.0 <= 5.0
        assert results["Professionalism"]["identify_self"]["passed"] is True
        assert results["Empathy"]["requires_apology_if_negative_sentiment"]["passed"] is True
        assert results["Compliance"]["requires_account_verification"]["passed"] is True
        assert results["Compliance"]["required_disclosures"]["passed"]["missing"] == []

        assert metrics["rules_evaluated"] == 5
        assert metrics["errors"] == 0
