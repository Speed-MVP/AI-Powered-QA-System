"""
JSON Schema Validator for LLM Responses
MVP Evaluation Improvements - Phase 2
"""

import json
from typing import Dict, Any, Tuple, Optional
from jsonschema import validate, ValidationError
import logging

logger = logging.getLogger(__name__)


class SchemaValidator:
    """
    Validates LLM evaluation responses against the strict JSON schema.
    Rejects invalid responses and provides detailed error information.
    """

    def __init__(self):
        self.schema = self._get_evaluation_schema()

    def _get_evaluation_schema(self) -> Dict[str, Any]:
        """Return the strict JSON schema for LLM evaluation responses."""
        return {
            "type": "object",
            "required": [
                "overall_score",
                "category_scores",
                "violations",
                "resolution",
                "explanations",
                "model_metadata"
            ],
            "properties": {
                "overall_score": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 100
                },
                "category_scores": {
                    "type": "object",
                    "patternProperties": {
                        "^.+$": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 100
                        }
                    }
                },
                "violations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["rule_id", "description", "severity", "evidence"],
                        "properties": {
                            "rule_id": {"type": "string"},
                            "description": {"type": "string"},
                            "severity": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 10
                            },
                            "evidence": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "speaker": {"type": "string"},
                                        "text": {"type": "string"},
                                        "start": {"type": "number"},
                                        "end": {"type": "number"}
                                    }
                                }
                            }
                        }
                    }
                },
                "resolution": {
                    "type": "string",
                    "enum": ["resolved", "unresolved", "partial"]
                },
                "explanations": {
                    "type": "object",
                    "additionalProperties": {"type": "string"}
                },
                "model_metadata": {
                    "type": "object",
                    "required": ["model_id", "model_version", "prompt_id", "prompt_version"],
                    "properties": {
                        "model_id": {"type": "string"},
                        "model_version": {"type": "string"},
                        "prompt_id": {"type": "string"},
                        "prompt_version": {"type": "string"},
                        "temperature": {"type": "number"},
                        "top_p": {"type": "number"},
                        "tokens_used": {"type": "number"},
                        "cost_estimate": {"type": "number"}
                    }
                }
            }
        }

    def validate_evaluation_response(self, response_json: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate LLM evaluation response against schema.

        Args:
            response_json: The parsed JSON response from LLM

        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if response matches schema
            - error_message: None if valid, error description if invalid
        """
        try:
            validate(instance=response_json, schema=self.schema)
            logger.info("LLM response schema validation: PASSED")
            return True, None
        except ValidationError as e:
            error_msg = f"Schema validation failed: {e.message}"
            if e.absolute_path:
                error_msg += f" at path: {'/'.join(str(p) for p in e.absolute_path)}"
            logger.warning(f"LLM response schema validation: FAILED - {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected validation error: {str(e)}"
            logger.error(f"LLM response schema validation: ERROR - {error_msg}")
            return False, error_msg

    def validate_and_extract_scores(self, response_json: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Validate response and extract scoring data if valid.

        Args:
            response_json: The parsed JSON response from LLM

        Returns:
            Tuple of (is_valid, extracted_data)
            - extracted_data contains: overall_score, category_scores, violations, resolution
        """
        is_valid, error_msg = self.validate_evaluation_response(response_json)

        if not is_valid:
            return False, None

        try:
            extracted_data = {
                "overall_score": response_json["overall_score"],
                "category_scores": response_json["category_scores"],
                "violations": response_json["violations"],
                "resolution": response_json["resolution"],
                "explanations": response_json.get("explanations", {}),
                "model_metadata": response_json["model_metadata"]
            }
            return True, extracted_data
        except KeyError as e:
            error_msg = f"Missing required field in validated response: {e}"
            logger.error(f"Data extraction failed: {error_msg}")
            return False, None

    def get_schema_summary(self) -> str:
        """Return a human-readable summary of the schema requirements."""
        return """
LLM Evaluation Response Schema Requirements:
- overall_score: Number 0-100
- category_scores: Object with category names as keys, scores 0-100 as values
- violations: Array of violation objects (rule_id, description, severity 0-10, evidence)
- resolution: Enum ["resolved", "unresolved", "partial"]
- explanations: Object with explanation strings
- model_metadata: Object with model_id, model_version, prompt_id, prompt_version
        """.strip()
