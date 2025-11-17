"""
Phase 2: Policy Rule Builder - Unit Tests
Deterministic QA System Redesign
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from app.services.policy_rule_builder import PolicyRuleBuilder
from app.models.policy_rule_models import PolicyRules, BooleanRule, NumericRule, ListRule


class TestPolicyRuleBuilder:
    """Test suite for PolicyRuleBuilder service."""

    @pytest.fixture
    def rule_builder(self):
        """Create a PolicyRuleBuilder instance."""
        return PolicyRuleBuilder()

    @pytest.fixture
    def sample_policy_text(self):
        """Sample policy text for testing."""
        return "Agent must greet customer within 15 seconds and identify themselves. Show empathy when customer is frustrated."

    @pytest.fixture
    def sample_rubric_levels(self):
        """Sample rubric levels for testing."""
        return {
            "Professionalism": [
                {"level_name": "Excellent", "min_score": 90, "max_score": 100, "description": "Perfect execution"},
                {"level_name": "Good", "min_score": 70, "max_score": 89, "description": "Solid performance"}
            ],
            "Empathy": [
                {"level_name": "Excellent", "min_score": 90, "max_score": 100, "description": "Shows genuine empathy"}
            ]
        }

    @pytest.fixture
    def mock_llm_response(self):
        """Mock LLM response for testing."""
        return {
            "response": json.dumps({
                "policy_rules": {
                    "Professionalism": [
                        {
                            "id": "greet_within_seconds",
                            "type": "numeric",
                            "value": 15,
                            "comparator": "le",
                            "description": "Agent must greet within 15 seconds"
                        },
                        {
                            "id": "identify_self",
                            "type": "boolean",
                            "value": True,
                            "description": "Agent must identify themselves"
                        }
                    ],
                    "Empathy": [
                        {
                            "id": "requires_apology_if_negative_sentiment",
                            "type": "boolean",
                            "value": True,
                            "description": "Agent must show empathy when customer sentiment is negative"
                        }
                    ]
                },
                "clarifications": []
            }),
            "model": "gemini-2.0-flash-exp",
            "tokens_used": 150,
            "latency_ms": 1200
        }

    def test_initialization(self, rule_builder):
        """Test PolicyRuleBuilder initialization."""
        assert rule_builder.gemini is not None
        assert rule_builder.validator is not None
        assert rule_builder.prompt_template is not None
        assert "Policy Rule Extractor" in rule_builder.prompt_template

    def test_build_prompt(self, rule_builder, sample_policy_text, sample_rubric_levels):
        """Test prompt building."""
        input_data = {
            "policy_text": sample_policy_text,
            "rubric_levels": sample_rubric_levels,
            "examples": "Sample call transcript...",
            "user_answers": {}
        }

        prompt = rule_builder._build_prompt(input_data)

        assert sample_policy_text in prompt
        assert "Sample call transcript" in prompt
        # Check that rubric levels are included (formatting may vary)
        assert "Professionalism" in prompt
        assert "Empathy" in prompt
        assert "Excellent" in prompt
        assert "Policy Rule Extractor" in prompt

    def test_parse_llm_response_valid(self, rule_builder):
        """Test parsing valid LLM response."""
        raw_response = json.dumps({
            "policy_rules": {
                "Professionalism": [
                    {
                        "id": "greet_within_seconds",
                        "type": "numeric",
                        "value": 15,
                        "comparator": "le",
                        "description": "Agent must greet within 15 seconds"
                    }
                ]
            },
            "clarifications": [
                {"id": "q1", "question": "What greeting methods are acceptable?"}
            ]
        })

        parsed = rule_builder._parse_llm_response(raw_response)

        assert "policy_rules" in parsed
        assert "clarifications" in parsed
        assert len(parsed["clarifications"]) == 1
        assert parsed["clarifications"][0]["id"] == "q1"

    def test_parse_llm_response_invalid_json(self, rule_builder):
        """Test parsing invalid JSON response."""
        with pytest.raises(ValueError) as exc_info:
            rule_builder._parse_llm_response("invalid json")

        assert "Invalid JSON response" in str(exc_info.value)

    def test_parse_llm_response_missing_policy_rules(self, rule_builder):
        """Test parsing response missing policy_rules."""
        raw_response = json.dumps({"clarifications": []})

        with pytest.raises(ValueError) as exc_info:
            rule_builder._parse_llm_response(raw_response)

        assert "policy_rules" in str(exc_info.value)

    def test_parse_llm_response_markdown_formatting(self, rule_builder):
        """Test parsing response with markdown code block formatting."""
        raw_response = """```json
{
  "policy_rules": {
    "Professionalism": [
      {"id": "test_rule", "type": "boolean", "value": true, "description": "Test rule"}
    ]
  },
  "clarifications": []
}
```"""

        parsed = rule_builder._parse_llm_response(raw_response)

        assert "policy_rules" in parsed
        assert len(parsed["policy_rules"]["Professionalism"]) == 1

    @patch('app.services.policy_rule_builder.PolicyRuleBuilder._parse_llm_response')
    def test_generate_policy_rules_success(self, mock_parse, rule_builder, sample_policy_text, mock_llm_response):
        """Test successful policy rules generation."""
        mock_parse.return_value = json.loads(mock_llm_response["response"])

        with patch.object(rule_builder.gemini, 'call_llm', return_value=mock_llm_response):
            llm_response, metadata = rule_builder.generate_policy_rules(sample_policy_text)

            assert "policy_rules" in llm_response
            assert "clarifications" in llm_response
            assert metadata["llm_model"] == "gemini-2.0-flash-exp"
            assert metadata["llm_tokens_used"] == 150
            assert metadata["llm_latency_ms"] >= 0  # Latency can vary
            assert "llm_prompt_hash" in metadata

    def test_validate_generated_rules_valid(self, rule_builder):
        """Test validation of valid generated rules."""
        valid_rules = {
            "Professionalism": [
                {
                    "id": "greet_within_seconds",
                    "type": "numeric",
                    "value": 15,
                    "comparator": "le",
                    "description": "Agent must greet within 15 seconds"
                }
            ]
        }

        is_valid, normalized, errors = rule_builder.validate_generated_rules(valid_rules)

        assert is_valid is True
        assert isinstance(normalized, PolicyRules)
        assert len(errors) == 0
        assert len(normalized.rules["Professionalism"]) == 1

    def test_validate_generated_rules_invalid(self, rule_builder):
        """Test validation of invalid generated rules."""
        invalid_rules = {
            "Professionalism": [
                {
                    "id": "invalid_rule_id_with_spaces and caps",
                    "type": "invalid_type",
                    "value": "invalid_value"
                }
            ]
        }

        is_valid, normalized, errors = rule_builder.validate_generated_rules(invalid_rules)

        assert is_valid is False
        assert normalized is None
        assert len(errors) > 0

    def test_extract_policy_text_from_template(self, rule_builder):
        """Test extracting policy text from template data."""
        template_data = {
            "description": "General policy description",
            "criteria": [
                {
                    "category_name": "Professionalism",
                    "evaluation_prompt": "Agent must be professional"
                },
                {
                    "category_name": "Empathy",
                    "evaluation_prompt": "Agent must show empathy"
                }
            ]
        }

        policy_text = rule_builder.extract_policy_text_from_template(template_data)

        assert "General policy description" in policy_text
        assert "Professionalism: Agent must be professional" in policy_text
        assert "Empathy: Agent must show empathy" in policy_text

    def test_extract_rubric_levels(self, rule_builder, sample_rubric_levels):
        """Test extracting rubric levels from template data."""
        template_data = {
            "criteria": [
                {
                    "category_name": "Professionalism",
                    "rubric_levels": sample_rubric_levels["Professionalism"]
                }
            ]
        }

        rubric_data = rule_builder.extract_rubric_levels(template_data)

        assert "Professionalism" in rubric_data
        assert len(rubric_data["Professionalism"]) == 2
        assert rubric_data["Professionalism"][0]["level_name"] == "Excellent"

    def test_hash_prompt(self, rule_builder):
        """Test prompt hashing for reproducibility."""
        prompt1 = "Test prompt"
        prompt2 = "Test prompt"
        prompt3 = "Different prompt"

        hash1 = rule_builder._hash_prompt(prompt1)
        hash2 = rule_builder._hash_prompt(prompt2)
        hash3 = rule_builder._hash_prompt(prompt3)

        assert hash1 == hash2  # Same prompt should have same hash
        assert hash1 != hash3  # Different prompts should have different hashes
        assert len(hash1) == 64  # SHA-256 hex length
