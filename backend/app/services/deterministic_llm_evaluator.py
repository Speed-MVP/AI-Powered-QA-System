"""
Phase 4: Deterministic LLM Evaluator (Rubric-Level Classifier)
Converts LLM role to strict rubric-level classifier with zero subjectivity.

This service handles:
- Structured input construction for LLM
- Deterministic prompt building
- LLM output validation and parsing
- Score calculation and penalty application
- Critical rule override logic
"""

import json
import hashlib
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from app.services.gemini import GeminiService
from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class LLMEvaluationInput:
    """Structured input for deterministic LLM evaluation."""
    evaluation_id: str
    policy_template_id: str
    policy_rules_version: Optional[int]
    categories: List[str]
    rubric_levels: Dict[str, List[str]]
    policy_results: Dict[str, Any]
    tone_flags: Dict[str, bool]
    transcript_summary: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "evaluation_id": self.evaluation_id,
            "policy_template_id": self.policy_template_id,
            "policy_rules_version": f"v{self.policy_rules_version}" if self.policy_rules_version else None,
            "categories": self.categories,
            "rubric_levels": self.rubric_levels,
            "policy_results": self.policy_results,
            "tone_flags": self.tone_flags,
            "transcript_summary": self.transcript_summary
        }


@dataclass
class LLMEvaluationResult:
    """Parsed and validated LLM evaluation result."""
    evaluation_id: str
    policy_template_id: str
    results: Dict[str, str]  # category -> rubric_level
    llm_meta: Dict[str, Any]
    raw_response: str
    prompt_hash: str
    execution_time_ms: int
    tokens_used: Optional[int]


class DeterministicLLMEvaluator:
    """
    Deterministic LLM evaluator that converts structured inputs to rubric levels.

    Key principles:
    - Zero subjectivity in LLM responses
    - Strict schema validation
    - Deterministic prompt building
    - Reproducible outputs with seeding
    """

    def __init__(self):
        self.use_mock_llm = settings.use_mock_llm or not settings.gemini_api_key
        self.gemini = None if self.use_mock_llm else GeminiService()
        self.prompt_template = self._load_prompt_template()
        self.output_schema = self._load_output_schema()

    def _load_prompt_template(self) -> str:
        """Load the deterministic prompt template."""
        return """You are a strict Rubric-Level Classifier. Input is structured JSON. Output must be a JSON object mapping categories to exactly one rubric level each, chosen from the provided rubric_levels. Do not output text, explanations, or additional fields. Choose the level that best matches the deterministic flags and summary.

Examples:
Input policy_results: {"Professionalism":{"greet_within_seconds":{"passed":true,"value":5}}}
Output: {"Professionalism":"Excellent"}

Input policy_results: {"Professionalism":{"greet_within_seconds":{"passed":false,"value":25}}}
Output: {"Professionalism":"Poor"}

Task: For each category in "categories", output the selected rubric level as the exact string from rubric_levels. Output JSON only."""

    def _load_output_schema(self) -> Dict[str, Any]:
        """Define the strict output schema for LLM responses."""
        return {
            "type": "object",
            "properties": {
                "evaluation_id": {"type": "string"},
                "policy_template_id": {"type": "string"},
                "results": {
                    "type": "object",
                    "patternProperties": {
                        ".*": {"type": "string"}  # category -> rubric_level
                    }
                },
                "llm_meta": {
                    "type": "object",
                    "properties": {
                        "model": {"type": "string"},
                        "model_version": {"type": "string"},
                        "temperature": {"type": "number"},
                        "top_p": {"type": "number"},
                        "seed": {"type": "string"}
                    }
                }
            },
            "required": ["evaluation_id", "policy_template_id", "results", "llm_meta"]
        }

    def build_evaluation_input(
        self,
        evaluation_id: str,
        policy_template_id: str,
        categories: List[str],
        rubric_levels: Dict[str, List[str]],
        policy_results: Dict[str, Any],
        tone_flags: Dict[str, bool],
        transcript_summary: Dict[str, Any],
        policy_rules_version: Optional[int] = None
    ) -> LLMEvaluationInput:
        """
        Build structured input for LLM evaluation.

        Args:
            evaluation_id: Unique evaluation identifier
            policy_template_id: Policy template identifier
            categories: List of categories to evaluate
            rubric_levels: Available rubric levels per category
            policy_results: Deterministic rule evaluation results
            tone_flags: Tone analysis flags
            transcript_summary: Compressed transcript summary
            policy_rules_version: Version of policy rules used

        Returns:
            Structured input object
        """
        return LLMEvaluationInput(
            evaluation_id=evaluation_id,
            policy_template_id=policy_template_id,
            policy_rules_version=policy_rules_version,
            categories=categories,
            rubric_levels=rubric_levels,
            policy_results=policy_results,
            tone_flags=tone_flags,
            transcript_summary=transcript_summary
        )

    def evaluate_recording(
        self,
        evaluation_input: LLMEvaluationInput,
        max_retries: int = 3
    ) -> Tuple[LLMEvaluationResult, Dict[str, Any]]:
        """
        Evaluate recording using deterministic LLM classification.

        Args:
            evaluation_input: Structured input for evaluation
            max_retries: Maximum retry attempts for failures

        Returns:
            Tuple of (parsed_result, metadata_dict)
        """
        start_time = time.time()

        # Build deterministic prompt
        prompt = self._build_prompt(evaluation_input)
        prompt_hash = self._hash_prompt(prompt)

        if self.use_mock_llm:
            logger.info("🧪 Using mock LLM evaluation (fast mode enabled)")
            parsed_result = self._build_mock_llm_result(
                evaluation_input,
                prompt_hash,
                int((time.time() - start_time) * 1000)
            )
            metadata = {
                "attempts_used": 1,
                "execution_time_ms": parsed_result.execution_time_ms,
                "tokens_used": parsed_result.tokens_used,
                "prompt_hash": prompt_hash,
                "model": parsed_result.llm_meta.get("model", "mock")
            }
            return parsed_result, metadata

        # LLM call with deterministic settings
        last_error = None
        for attempt in range(max_retries):
            try:
                logger.info(f"LLM evaluation attempt {attempt + 1}/{max_retries} for {evaluation_input.evaluation_id}")

                llm_response = self.gemini.call_llm(
                    prompt=prompt,
                    temperature=0.0,  # Deterministic
                    top_p=0.0,        # No nucleus sampling
                    max_tokens=500,   # Small response expected
                    model="gemini-2.0-flash-exp",  # Fast model
                    seed=evaluation_input.evaluation_id  # Deterministic seeding
                )

                # Parse and validate response
                parsed_result = self._parse_and_validate_response(
                    llm_response["response"],
                    evaluation_input,
                    prompt_hash,
                    int((time.time() - start_time) * 1000)
                )

                # Add LLM metadata
                parsed_result.llm_meta.update({
                    "tokens_used": llm_response.get("tokens_used")
                })

                metadata = {
                    "attempts_used": attempt + 1,
                    "execution_time_ms": parsed_result.execution_time_ms,
                    "tokens_used": parsed_result.tokens_used,
                    "prompt_hash": prompt_hash,
                    "model": parsed_result.llm_meta.get("model", "unknown")
                }

                logger.info(
                    f"LLM evaluation successful for {evaluation_input.evaluation_id}: "
                    f"{len(parsed_result.results)} categories in {parsed_result.execution_time_ms}ms"
                )

                return parsed_result, metadata

            except Exception as e:
                last_error = e
                logger.warning(f"LLM evaluation attempt {attempt + 1} failed: {e}")

                # Exponential backoff for retries
                if attempt < max_retries - 1:
                    delay = 1 * (3 ** attempt)  # 1s, 3s, 9s
                    time.sleep(delay)

        # All retries failed
        raise Exception(f"LLM evaluation failed after {max_retries} attempts: {last_error}")

    def _build_prompt(self, evaluation_input: LLMEvaluationInput) -> str:
        """Build deterministic prompt with canonical JSON formatting."""
        input_dict = evaluation_input.to_dict()

        # Canonical JSON formatting for determinism
        input_json = json.dumps(input_dict, sort_keys=True, separators=(',', ':'))

        return f"{self.prompt_template}\n\nInput: {input_json}"

    def _parse_and_validate_response(
        self,
        raw_response: str,
        evaluation_input: LLMEvaluationInput,
        prompt_hash: str,
        execution_time_ms: int
    ) -> LLMEvaluationResult:
        """
        Parse and validate LLM response against strict schema.

        Args:
            raw_response: Raw LLM text response
            evaluation_input: Original input for validation
            prompt_hash: Hash of prompt used
            execution_time_ms: Total execution time

        Returns:
            Validated and parsed result

        Raises:
            ValueError: If response is invalid
        """
        try:
            # Clean response (remove markdown if present)
            cleaned_response = raw_response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()

            parsed = json.loads(cleaned_response)

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from LLM: {e}")

        # Validate against schema
        self._validate_response_schema(parsed, evaluation_input)

        return LLMEvaluationResult(
            evaluation_id=parsed["evaluation_id"],
            policy_template_id=parsed["policy_template_id"],
            results=parsed["results"],
            llm_meta=parsed["llm_meta"],
            raw_response=raw_response,
            prompt_hash=prompt_hash,
            execution_time_ms=execution_time_ms,
            tokens_used=None  # Will be set by caller
        )

    def _validate_response_schema(self, parsed: Dict[str, Any], evaluation_input: LLMEvaluationInput) -> None:
        """
        Validate LLM response against strict schema requirements.

        Args:
            parsed: Parsed JSON response
            evaluation_input: Original input for cross-validation

        Raises:
            ValueError: If validation fails
        """
        # Required top-level fields
        required_fields = ["evaluation_id", "policy_template_id", "results", "llm_meta"]
        for field in required_fields:
            if field not in parsed:
                raise ValueError(f"Missing required field: {field}")

        # Evaluation ID must match input
        if parsed["evaluation_id"] != evaluation_input.evaluation_id:
            raise ValueError(f"evaluation_id mismatch: expected {evaluation_input.evaluation_id}, got {parsed['evaluation_id']}")

        # Policy template ID must match input
        if parsed["policy_template_id"] != evaluation_input.policy_template_id:
            raise ValueError(f"policy_template_id mismatch: expected {evaluation_input.policy_template_id}, got {parsed['policy_template_id']}")

        # Results must contain exactly the expected categories
        if set(parsed["results"].keys()) != set(evaluation_input.categories):
            raise ValueError(f"Results categories mismatch: expected {evaluation_input.categories}, got {list(parsed['results'].keys())}")

        # Each rubric level must be valid for its category
        for category, level in parsed["results"].items():
            if category not in evaluation_input.rubric_levels:
                raise ValueError(f"Unknown category in results: {category}")

            if level not in evaluation_input.rubric_levels[category]:
                raise ValueError(f"Invalid rubric level '{level}' for category '{category}'. Valid levels: {evaluation_input.rubric_levels[category]}")

        # LLM meta validation
        llm_meta = parsed["llm_meta"]
        required_meta = ["model", "temperature", "top_p"]
        for field in required_meta:
            if field not in llm_meta:
                raise ValueError(f"Missing LLM meta field: {field}")

        # Temperature and top_p must be 0.0 for determinism
        if llm_meta["temperature"] != 0.0 or llm_meta["top_p"] != 0.0:
            raise ValueError("LLM must use temperature=0.0 and top_p=0.0 for deterministic results")

    def _hash_prompt(self, prompt: str) -> str:
        """Generate SHA-256 hash of prompt for reproducibility tracking."""
        return hashlib.sha256(prompt.encode('utf-8')).hexdigest()

    def _build_mock_llm_result(
        self,
        evaluation_input: LLMEvaluationInput,
        prompt_hash: str,
        execution_time_ms: int
    ) -> LLMEvaluationResult:
        """Generate deterministic mock results for fast local development."""
        results = {}
        for category in evaluation_input.categories:
            levels = evaluation_input.rubric_levels.get(category, ["Average"])
            default_level = levels[0] if levels else "Average"
            fallback_level = levels[-1] if levels else "Average"

            category_rules = evaluation_input.policy_results.get(category, {})
            has_failure = any(
                isinstance(result, dict) and result.get("passed") is False
                for result in category_rules.values()
            )

            results[category] = fallback_level if has_failure else default_level

        mock_payload = {
            "evaluation_id": evaluation_input.evaluation_id,
            "policy_template_id": evaluation_input.policy_template_id,
            "results": results,
            "llm_meta": {
                "model": "mock-llm",
                "model_version": "v1",
                "temperature": 0.0,
                "top_p": 0.0,
                "seed": evaluation_input.evaluation_id,
                "mock": True
            }
        }

        raw_response = json.dumps(mock_payload)

        return LLMEvaluationResult(
            evaluation_id=evaluation_input.evaluation_id,
            policy_template_id=evaluation_input.policy_template_id,
            results=results,
            llm_meta=mock_payload["llm_meta"],
            raw_response=raw_response,
            prompt_hash=prompt_hash,
            execution_time_ms=execution_time_ms,
            tokens_used=0
        )

    def apply_critical_overrides(
        self,
        llm_results: Dict[str, str],
        policy_results: Dict[str, Any],
        policy_rules: Dict[str, Any]
    ) -> Tuple[Dict[str, str], List[Dict[str, Any]]]:
        """
        Apply deterministic overrides for critical rule failures.

        Args:
            llm_results: LLM-selected rubric levels
            policy_results: Deterministic rule evaluation results
            policy_rules: Policy rules configuration

        Returns:
            Tuple of (final_results, overrides_applied)
        """
        final_results = llm_results.copy()
        overrides_applied = []

        # Check for critical rule failures that require overrides
        for category_name, category_rules in policy_rules.get("rules", {}).items():
            if category_name not in policy_results:
                continue

            category_policy_results = policy_results[category_name]

            # Check each rule in the category
            for rule in category_rules:
                rule_id = rule.get("id")
                if not rule_id or rule_id not in category_policy_results:
                    continue

                rule_result = category_policy_results[rule_id]

                # Check if this is a critical rule that failed
                is_critical = rule.get("critical", False)
                passed = rule_result.get("passed", True)

                if is_critical and not passed:
                    # Override to Unacceptable
                    old_level = final_results.get(category_name)
                    final_results[category_name] = "Unacceptable"

                    overrides_applied.append({
                        "category": category_name,
                        "rule_id": rule_id,
                        "old_level": old_level,
                        "forced_level": "Unacceptable",
                        "reason": f"Critical rule '{rule_id}' failed"
                    })

                    logger.warning(
                        f"Critical rule override applied: {category_name}.{rule_id} failed, "
                        f"forcing level to Unacceptable (was {old_level})"
                    )

        return final_results, overrides_applied
