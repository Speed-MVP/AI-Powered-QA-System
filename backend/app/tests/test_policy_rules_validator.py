"""
Phase 1: Structured Rules Layer - Unit Tests for PolicyRulesValidator
Deterministic QA System Redesign
"""

import pytest
from unittest.mock import patch, mock_open
from app.services.policy_rules_validator import PolicyRulesValidator, ValidationError
from app.models.policy_rule_models import BooleanRule, NumericRule, ListRule, PolicyRules
from app.models.user import User, UserRole


class TestPolicyRulesValidator:
    """Test suite for PolicyRulesValidator service."""

    @pytest.fixture
    def validator(self):
        """Create a validator instance."""
        return PolicyRulesValidator()

    @pytest.fixture
    def valid_policy_rules_json(self):
        """Valid policy rules JSON for testing."""
        return {
            "rules": {
                "Professionalism": [
                    {
                        "id": "greet_within_seconds",
                        "description": "Agent must greet within 15 seconds",
                        "type": "numeric",
                        "value": 15.0,
                        "comparator": "le"
                    },
                    {
                        "id": "identify_self",
                        "description": "Agent must identify themselves",
                        "type": "boolean",
                        "value": True
                    }
                ],
                "Empathy": [
                    {
                        "id": "apology_keywords",
                        "description": "Must use apology keywords",
                        "type": "list",
                        "items": ["sorry", "apologize", "my apologies"]
                    }
                ]
            }
        }

    def test_validate_policy_rules_valid(self, validator, valid_policy_rules_json):
        """Test validation of valid policy rules."""
        with patch('app.services.policy_rules_validator.jsonschema.validate'):
            result = validator.validate_policy_rules(valid_policy_rules_json)

            assert isinstance(result, PolicyRules)
            assert len(result.rules) == 2
            assert "Professionalism" in result.rules
            assert "Empathy" in result.rules
            assert len(result.rules["Professionalism"]) == 2
            assert len(result.rules["Empathy"]) == 1

            # Check first rule
            greet_rule = result.rules["Professionalism"][0]
            assert isinstance(greet_rule, NumericRule)
            assert greet_rule.id == "greet_within_seconds"
            assert greet_rule.value == 15.0
            assert greet_rule.comparator == "le"

            # Check boolean rule
            bool_rule = result.rules["Professionalism"][1]
            assert isinstance(bool_rule, BooleanRule)
            assert bool_rule.id == "identify_self"
            assert bool_rule.value is True

            # Check list rule
            list_rule = result.rules["Empathy"][0]
            assert isinstance(list_rule, ListRule)
            assert list_rule.id == "apology_keywords"
            assert list_rule.items == ["sorry", "apologize", "my apologies"]

    def test_validate_policy_rules_invalid_json(self, validator):
        """Test validation with invalid JSON structure."""
        invalid_json = {"invalid": "structure"}

        # Should raise ValidationError because "rules" is required
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_policy_rules(invalid_json)

        assert "rules" in str(exc_info.value).lower()

        assert "Policy rules validation failed" in str(exc_info.value)

    def test_validate_policy_rules_missing_required_fields(self, validator):
        """Test validation with missing required fields."""
        invalid_json = {
            "rules": {
                "Test": [
                    {
                        "id": "missing_type",
                        "description": "Missing type field"
                        # Missing "type" field
                    }
                ]
            }
        }

        with pytest.raises(ValidationError):
            validator.validate_policy_rules(invalid_json)

    def test_normalize_policy_rules_invalid_comparator(self, validator):
        """Test normalization with invalid comparator."""
        invalid_json = {
            "rules": {
                "Test": [
                    {
                        "id": "invalid_comparator",
                        "type": "numeric",
                        "value": 10.0,
                        "comparator": "invalid"
                    }
                ]
            }
        }

        with pytest.raises(ValidationError) as exc_info:
            validator.validate_policy_rules(invalid_json)

        assert "comparator" in str(exc_info.value).lower()

    def test_normalize_policy_rules_empty_list_rule(self, validator):
        """Test normalization with empty list rule."""
        invalid_json = {
            "rules": {
                "Test": [
                    {
                        "id": "empty_list",
                        "type": "list",
                        "items": []
                    }
                ]
            }
        }

        with pytest.raises(ValidationError) as exc_info:
            validator.validate_policy_rules(invalid_json)

        assert "items" in str(exc_info.value).lower()

    def test_is_editable_by_user_admin(self, validator):
        """Test authorization for admin user."""
        admin_user = User(id="admin1", role=UserRole.admin, company_id="company1")

        assert validator.is_editable_by_user(admin_user, "company1") is True

    def test_is_editable_by_user_qa_manager(self, validator):
        """Test authorization for QA manager user."""
        qa_user = User(id="qa1", role=UserRole.qa_manager, company_id="company1")

        assert validator.is_editable_by_user(qa_user, "company1") is True

    def test_is_editable_by_user_wrong_role(self, validator):
        """Test authorization denied for wrong role."""
        regular_user = User(id="user1", role=UserRole.reviewer, company_id="company1")

        assert validator.is_editable_by_user(regular_user, "company1") is False

    def test_is_editable_by_user_wrong_company(self, validator):
        """Test authorization denied for wrong company."""
        admin_user = User(id="admin1", role=UserRole.admin, company_id="company1")

        assert validator.is_editable_by_user(admin_user, "company2") is False

    def test_validate_rule_payload_size_valid(self, validator):
        """Test payload size validation within limits."""
        small_payload = {"rules": {"Test": [{"id": "test", "type": "boolean", "value": True}]}}

        assert validator.validate_rule_payload_size(small_payload) is True

    def test_validate_rule_payload_size_too_large(self, validator):
        """Test payload size validation exceeding limits."""
        # Create a payload larger than 50KB
        large_items = ["item"] * 10000
        large_payload = {
            "rules": {
                "Test": [{
                    "id": "large_list",
                    "type": "list",
                    "items": large_items
                }]
            }
        }

        assert validator.validate_rule_payload_size(large_payload) is False

    def test_serialize_policy_rules(self, validator, valid_policy_rules_json):
        """Test serialization of PolicyRules back to JSON."""
        with patch('app.services.policy_rules_validator.jsonschema.validate'):
            policy_rules = validator.validate_policy_rules(valid_policy_rules_json)
            serialized = validator.serialize_policy_rules(policy_rules)

            assert "rules" in serialized
            assert "Professionalism" in serialized["rules"]
            assert "Empathy" in serialized["rules"]

            # Check that first rule has type field added
            first_rule = serialized["rules"]["Professionalism"][0]
            assert first_rule["type"] == "numeric"
            assert first_rule["id"] == "greet_within_seconds"

    def test_get_schema(self, validator):
        """Test schema retrieval."""
        schema = validator.get_schema()
        assert isinstance(schema, dict)
        assert "type" in schema  # Basic structure check
        assert "properties" in schema
        assert "definitions" in schema
        assert "title" in schema

    @pytest.mark.parametrize("rule_type,expected_class", [
        ("boolean", BooleanRule),
        ("numeric", NumericRule),
        ("list", ListRule),
    ])
    def test_normalize_different_rule_types(self, validator, rule_type, expected_class):
        """Test normalization of different rule types."""
        test_json = {
            "rules": {
                "Test": [
                    {
                        "id": f"test_{rule_type}",
                        "type": rule_type,
                        "value": True if rule_type == "boolean" else 10.0 if rule_type == "numeric" else None,
                        "items": ["test"] if rule_type == "list" else None,
                        "comparator": "le" if rule_type == "numeric" else None
                    }
                ]
            }
        }

        # Remove None values for cleaner JSON
        rule = test_json["rules"]["Test"][0]
        test_json["rules"]["Test"][0] = {k: v for k, v in rule.items() if v is not None}

        with patch('app.services.policy_rules_validator.jsonschema.validate'):
            result = validator.validate_policy_rules(test_json)

            assert len(result.rules["Test"]) == 1
            assert isinstance(result.rules["Test"][0], expected_class)
            assert result.rules["Test"][0].id == f"test_{rule_type}"
