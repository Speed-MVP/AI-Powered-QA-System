"""
Phase 1: Structured Rules Layer - Unit Tests for RuleEngineV2
Deterministic QA System Redesign
"""

import pytest
from app.services.rule_engine_v2 import RuleEngineV2
from app.models.policy_rule_models import (
    PolicyRules,
    BooleanRule,
    NumericRule,
    ListRule
)


class TestRuleEngineV2:
    """Test suite for RuleEngineV2 service."""

    @pytest.fixture
    def sample_policy_rules(self):
        """Create sample policy rules for testing."""
        return PolicyRules(rules={
            "Professionalism": [
                NumericRule(
                    id="greet_within_seconds",
                    description="Agent must greet within 15 seconds",
                    value=15.0,
                    comparator="le"
                ),
                BooleanRule(
                    id="identify_self",
                    description="Agent must identify themselves",
                    value=True
                )
            ],
            "Empathy": [
                ListRule(
                    id="apology_keywords",
                    description="Must use apology keywords",
                    items=["sorry", "apologize", "my apologies"]
                )
            ]
        })

    @pytest.fixture
    def rule_engine(self, sample_policy_rules):
        """Create a rule engine instance."""
        return RuleEngineV2(sample_policy_rules)

    @pytest.fixture
    def sample_transcript_segments(self):
        """Sample transcript segments for testing."""
        return [
            {
                "speaker": "agent",
                "text": "Hello, thank you for calling. This is John from support.",
                "start": 5.0,
                "end": 12.0
            },
            {
                "speaker": "caller",
                "text": "Hi, I'm having issues with my order.",
                "start": 13.0,
                "end": 18.0
            },
            {
                "speaker": "agent",
                "text": "I'm sorry to hear that. Let me help you with that.",
                "start": 19.0,
                "end": 25.0
            }
        ]

    @pytest.fixture
    def sample_metadata(self):
        """Sample call metadata for testing."""
        return {
            "call_duration": 120.0,
            "recording_start_time": "2024-01-01T10:00:00Z",
            "agent_id": "agent123",
            "team_id": "team456"
        }

    def test_initialization(self, rule_engine):
        """Test rule engine initialization."""
        assert rule_engine.policy_rules is not None
        assert len(rule_engine._sorted_rule_ids) == 3  # 3 rules total
        assert rule_engine._sorted_rule_ids[0] == ("Empathy", "apology_keywords")
        assert rule_engine._sorted_rule_ids[1] == ("Professionalism", "greet_within_seconds")
        assert rule_engine._sorted_rule_ids[2] == ("Professionalism", "identify_self")

    def test_evaluate_greet_within_seconds_pass(self, rule_engine, sample_transcript_segments, sample_metadata):
        """Test greet_within_seconds rule evaluation - pass case."""
        results = rule_engine.evaluate(sample_transcript_segments, sample_metadata)

        assert "Professionalism" in results
        assert "greet_within_seconds" in results["Professionalism"]
        rule_result = results["Professionalism"]["greet_within_seconds"]

        assert rule_result["passed"] is True
        assert "first_agent_utterance=5.0" in rule_result["evidence"]
        assert rule_result["value"] == 5.0

    def test_evaluate_greet_within_seconds_fail(self, rule_engine, sample_metadata):
        """Test greet_within_seconds rule evaluation - fail case."""
        # Agent greets too late
        late_segments = [
            {
                "speaker": "agent",
                "text": "Hello there!",
                "start": 20.0,  # After 15 second threshold
                "end": 22.0
            }
        ]

        results = rule_engine.evaluate(late_segments, sample_metadata)

        assert "Professionalism" in results
        rule_result = results["Professionalism"]["greet_within_seconds"]

        assert rule_result["passed"] is False
        assert "first_agent_utterance=20.0" in rule_result["evidence"]

    def test_evaluate_greet_within_seconds_no_agent(self, rule_engine, sample_metadata):
        """Test greet_within_seconds rule with no agent segments."""
        no_agent_segments = [
            {
                "speaker": "caller",
                "text": "Hello?",
                "start": 0.0,
                "end": 2.0
            }
        ]

        results = rule_engine.evaluate(no_agent_segments, sample_metadata)

        assert "Professionalism" in results
        rule_result = results["Professionalism"]["greet_within_seconds"]

        assert rule_result["passed"] is False
        assert "no agent utterance found" in rule_result["evidence"]

    def test_evaluate_boolean_rule(self, rule_engine, sample_transcript_segments, sample_metadata):
        """Test boolean rule evaluation."""
        results = rule_engine.evaluate(sample_transcript_segments, sample_metadata)

        assert "Professionalism" in results
        rule_result = results["Professionalism"]["identify_self"]

        # Boolean rules currently return placeholder results
        assert rule_result["passed"] is True  # Default boolean value
        assert "Boolean rule placeholder" in rule_result["evidence"][0]

    def test_evaluate_list_rule_pass(self, rule_engine, sample_transcript_segments, sample_metadata):
        """Test list rule evaluation - pass case."""
        results = rule_engine.evaluate(sample_transcript_segments, sample_metadata)

        assert "Empathy" in results
        rule_result = results["Empathy"]["apology_keywords"]

        assert rule_result["passed"] is True
        assert "sorry" in rule_result["evidence"]
        assert rule_result["value"] is True

    def test_evaluate_list_rule_fail(self, rule_engine, sample_metadata):
        """Test list rule evaluation - fail case."""
        # Transcript without apology keywords
        no_apology_segments = [
            {
                "speaker": "agent",
                "text": "Hello, how can I help you today?",
                "start": 5.0,
                "end": 10.0
            },
            {
                "speaker": "caller",
                "text": "I need help with my order.",
                "start": 11.0,
                "end": 15.0
            },
            {
                "speaker": "agent",
                "text": "Let me check that for you.",
                "start": 16.0,
                "end": 20.0
            }
        ]

        results = rule_engine.evaluate(no_apology_segments, sample_metadata)

        assert "Empathy" in results
        rule_result = results["Empathy"]["apology_keywords"]

        assert rule_result["passed"] is False
        assert "no required greeting phrases found" in rule_result["evidence"]

    def test_evaluate_call_duration_rule(self, rule_engine, sample_transcript_segments):
        """Test call duration rule evaluation."""
        # Add a call duration rule to test
        duration_rule = NumericRule(
            id="call_duration_max",
            description="Call must not exceed max duration",
            value=300.0,  # 5 minutes
            comparator="le"
        )

        rule_engine.policy_rules.rules["Compliance"] = [duration_rule]

        metadata = {"call_duration": 180.0}  # 3 minutes - should pass
        results = rule_engine.evaluate(sample_transcript_segments, metadata)

        assert "Compliance" in results
        rule_result = results["Compliance"]["call_duration_max"]

        assert rule_result["passed"] is True
        assert "call_duration=180.0" in rule_result["evidence"]

    def test_evaluate_with_empty_transcript(self, rule_engine, sample_metadata):
        """Test evaluation with empty transcript."""
        results = rule_engine.evaluate([], sample_metadata)

        assert len(results) == 3  # All categories should be present
        # Most rules should fail gracefully with appropriate evidence

    def test_evaluate_with_empty_metadata(self, rule_engine, sample_transcript_segments):
        """Test evaluation with empty metadata."""
        results = rule_engine.evaluate(sample_transcript_segments, {})

        # Should not crash, should use default values
        assert isinstance(results, dict)

    def test_numeric_comparators(self):
        """Test all numeric comparators work correctly."""
        test_cases = [
            ("le", 10.0, 15.0, True),   # 10 <= 15
            ("le", 20.0, 15.0, False),  # 20 <= 15
            ("lt", 10.0, 15.0, True),   # 10 < 15
            ("lt", 15.0, 15.0, False),  # 15 < 15
            ("ge", 20.0, 15.0, True),   # 20 >= 15
            ("ge", 10.0, 15.0, False),  # 10 >= 15
            ("gt", 20.0, 15.0, True),   # 20 > 15
            ("gt", 15.0, 15.0, False),  # 15 > 15
            ("eq", 15.0, 15.0, True),   # 15 == 15
            ("eq", 10.0, 15.0, False),  # 10 == 15
        ]

        rules = PolicyRules(rules={
            "Test": [
                NumericRule(id=f"test_{comp}_{i}", value=threshold, comparator=comp)
                for i, (comp, value, threshold, _) in enumerate(test_cases)
            ]
        })

        engine = RuleEngineV2(rules)

        for i, (comp, value, threshold, expected) in enumerate(test_cases):
            rule_id = f"test_{comp}_{i}"
            segments = [{"speaker": "agent", "text": "test", "start": 0.0}]

            # Mock the generic numeric evaluator to return the test value
            results = engine.evaluate(segments, {rule_id: value})

            # Find the result for this rule
            rule_result = None
            for category_results in results.values():
                if rule_id in category_results:
                    rule_result = category_results[rule_id]
                    break

            assert rule_result is not None
            assert rule_result["passed"] == expected

    def test_rule_evaluation_error_handling(self, rule_engine, sample_transcript_segments, sample_metadata):
        """Test that rule evaluation errors are handled gracefully."""
        # Add a rule that will cause an error
        error_rule = NumericRule(
            id="problematic_rule",
            value=float('inf'),  # This might cause issues
            comparator="le"
        )

        rule_engine.policy_rules.rules["Test"] = [error_rule]

        # Should not crash the entire evaluation
        results = rule_engine.evaluate(sample_transcript_segments, sample_metadata)

        assert "Test" in results
        rule_result = results["Test"]["problematic_rule"]

        assert rule_result["passed"] is False
        assert "Evaluation error" in rule_result["evidence"][0]

    def test_deterministic_evaluation_order(self, rule_engine, sample_transcript_segments, sample_metadata):
        """Test that rules are evaluated in deterministic order."""
        # Run evaluation multiple times
        results1 = rule_engine.evaluate(sample_transcript_segments, sample_metadata)
        results2 = rule_engine.evaluate(sample_transcript_segments, sample_metadata)

        # Results should be identical
        assert results1 == results2

        # Check that categories are in sorted order
        category_names = list(results1.keys())
        assert category_names == sorted(category_names)
