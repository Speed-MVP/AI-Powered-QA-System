"""
Phase 1: Structured Rules Layer - Policy Rules Validator Service
Deterministic QA System Redesign

Validates, normalizes, and authorizes policy rules for the rule engine.
"""

import json
import logging
import os
from typing import Dict, Any, Optional, Tuple
from dataclasses import asdict

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

from app.models.policy_rule_models import (
    BooleanRule,
    NumericRule,
    ListRule,
    PolicyRules,
    RULE_TYPE_BOOLEAN,
    RULE_TYPE_NUMERIC,
    RULE_TYPE_LIST,
    SUPPORTED_COMPARATORS
)
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when policy rules validation fails"""
    pass


class PolicyRulesValidator:
    """
    Validates and normalizes policy rules JSON according to the schema.
    Provides authorization checks for rule management operations.
    """

    def __init__(self):
        self.schema = self._load_schema()
        self._cached_normalized_rules = {}  # Cache for normalized rules

    def _load_schema(self) -> Dict[str, Any]:
        """Load the JSON schema for policy rules validation"""
        schema_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'schemas',
            'policy_rules.schema.json'
        )

        try:
            with open(schema_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Policy rules schema not found at {schema_path}")
            raise ValidationError("Policy rules schema file not found")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in policy rules schema: {e}")
            raise ValidationError("Invalid policy rules schema format")

    def validate_policy_rules(self, raw_json: Dict[str, Any]) -> PolicyRules:
        """
        Validate raw policy rules JSON and return normalized PolicyRules object.

        Args:
            raw_json: Raw policy rules JSON from request/database

        Returns:
            PolicyRules: Normalized and validated policy rules object

        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(raw_json, dict):
            raise ValidationError("Policy rules must be a JSON object")

        # Validate against JSON schema
        if HAS_JSONSCHEMA:
            try:
                jsonschema.validate(instance=raw_json, schema=self.schema)
            except jsonschema.ValidationError as e:
                error_msg = f"Policy rules validation failed: {e.message}"
                if e.absolute_path:
                    error_msg += f" at {'.'.join(str(p) for p in e.absolute_path)}"
                logger.error(error_msg)
                raise ValidationError(error_msg)
        else:
            logger.warning("jsonschema not available, skipping schema validation")

        # Normalize to typed objects
        try:
            normalized = self._normalize_policy_rules(raw_json)
            logger.info(f"Successfully validated and normalized {len(normalized.rules)} rule categories")
            return normalized
        except Exception as e:
            logger.error(f"Failed to normalize policy rules: {e}")
            raise ValidationError(f"Rule normalization failed: {str(e)}")

    def _normalize_policy_rules(self, raw_json: Dict[str, Any]) -> PolicyRules:
        """
        Convert raw JSON rules into typed dataclass objects.

        Args:
            raw_json: Validated raw JSON

        Returns:
            PolicyRules: Normalized rules with typed objects
        """
        normalized_rules = {}

        for category, rules_list in raw_json.get("rules", {}).items():
            normalized_rules[category] = []

            for rule_json in rules_list:
                rule_type = rule_json.get("type")

                try:
                    if rule_type == RULE_TYPE_BOOLEAN:
                        rule_obj = BooleanRule(
                            id=rule_json["id"],
                            description=rule_json.get("description"),
                            value=rule_json["value"]
                        )
                    elif rule_type == RULE_TYPE_NUMERIC:
                        comparator = rule_json.get("comparator", "le")
                        if comparator not in SUPPORTED_COMPARATORS:
                            raise ValidationError(f"Invalid comparator '{comparator}' for rule {rule_json['id']}")

                        rule_obj = NumericRule(
                            id=rule_json["id"],
                            description=rule_json.get("description"),
                            value=float(rule_json["value"]),
                            comparator=comparator
                        )
                    elif rule_type == RULE_TYPE_LIST:
                        items = rule_json.get("items", [])
                        if not items:
                            raise ValidationError(f"List rule {rule_json['id']} must have at least one item")

                        rule_obj = ListRule(
                            id=rule_json["id"],
                            description=rule_json.get("description"),
                            items=items
                        )
                    else:
                        raise ValidationError(f"Unknown rule type '{rule_type}' for rule {rule_json.get('id', 'unknown')}")

                    normalized_rules[category].append(rule_obj)

                except KeyError as e:
                    raise ValidationError(f"Missing required field '{e}' for rule {rule_json.get('id', 'unknown')}")
                except (ValueError, TypeError) as e:
                    raise ValidationError(f"Invalid value for rule {rule_json.get('id', 'unknown')}: {e}")

        return PolicyRules(rules=normalized_rules)

    def is_editable_by_user(self, user: User, template_company_id: str) -> bool:
        """
        Check if a user is authorized to edit policy rules for a template.

        Args:
            user: The user attempting to edit rules
            template_company_id: Company ID of the policy template

        Returns:
            bool: True if user can edit rules
        """
        # Only admin and qa_manager roles can edit policy rules
        if user.role not in [UserRole.admin, UserRole.qa_manager]:
            logger.warning(f"User {user.id} with role {user.role} denied access to edit policy rules")
            return False

        # Must belong to the same company as the template
        if user.company_id != template_company_id:
            logger.warning(f"User {user.id} from company {user.company_id} cannot edit template for company {template_company_id}")
            return False

        return True

    def get_schema(self) -> Dict[str, Any]:
        """
        Return the JSON schema for client-side validation.

        Returns:
            Dict: The policy rules JSON schema
        """
        return self.schema

    def serialize_policy_rules(self, policy_rules: PolicyRules) -> Dict[str, Any]:
        """
        Convert PolicyRules object back to JSON-serializable dict.

        Args:
            policy_rules: Normalized PolicyRules object

        Returns:
            Dict: JSON-serializable representation
        """
        result = {"rules": {}}

        for category, rules in policy_rules.rules.items():
            result["rules"][category] = []

            for rule in rules:
                rule_dict = asdict(rule)
                # Add type field based on class
                if isinstance(rule, BooleanRule):
                    rule_dict["type"] = RULE_TYPE_BOOLEAN
                elif isinstance(rule, NumericRule):
                    rule_dict["type"] = RULE_TYPE_NUMERIC
                elif isinstance(rule, ListRule):
                    rule_dict["type"] = RULE_TYPE_LIST

                # Remove None descriptions
                if rule_dict.get("description") is None:
                    del rule_dict["description"]

                result["rules"][category].append(rule_dict)

        return result

    def validate_rule_payload_size(self, raw_json: Dict[str, Any]) -> bool:
        """
        Check if the policy rules payload is within size limits.

        Args:
            raw_json: Raw policy rules JSON

        Returns:
            bool: True if within limits
        """
        # Limit to 50KB as specified
        json_str = json.dumps(raw_json, separators=(',', ':'))
        size_kb = len(json_str.encode('utf-8')) / 1024

        if size_kb > 50:
            logger.warning(f"Policy rules payload too large: {size_kb:.1f}KB (limit: 50KB)")
            return False

        return True



