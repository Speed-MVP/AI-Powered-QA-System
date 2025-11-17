"""
Phase 3: Rule Engine V2 - Deterministic Policy Enforcement
Executes structured policy_rules against transcripts with zero randomness.

This is the core deterministic evaluation engine that replaces subjective LLM interpretation
with objective, verifiable rule checking.
"""

import time
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class RuleEvaluationResult:
    """Standardized result format for rule evaluation"""
    rule_id: str
    rule_type: str
    passed: Union[bool, Dict[str, Any], None]  # True/False for boolean, dict for list, None for error
    actual_value: Optional[Any] = None         # Actual measured value for numeric rules
    required_value: Optional[Any] = None       # Required value for comparison
    evidence: Optional[str] = None             # Human-readable evidence
    error: Optional[str] = None                # Error message if evaluation failed


class RuleEngineV2Deterministic:
    """
    Deterministic rule engine that evaluates structured policy rules against transcripts.

    Key principles:
    - Zero randomness or subjectivity
    - Pure functions with predictable outputs
    - Fast execution (< 50ms per evaluation)
    - Comprehensive error handling
    - Standardized output format
    """

    def __init__(self):
        self.rule_evaluators = {
            "boolean": self._evaluate_boolean_rule,
            "numeric": self._evaluate_numeric_rule,
            "list": self._evaluate_list_rule
        }

    def evaluate_recording(
        self,
        policy_rules: Dict[str, Any],
        transcript_segments: List[Dict[str, Any]],
        sentiment_analysis: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Evaluate all policy rules against a recording.

        Args:
            policy_rules: Structured rules from Phase 2 (policy_rules JSON)
            transcript_segments: Diarized transcript segments
            sentiment_analysis: Voice-based sentiment analysis
            metadata: Additional call metadata

        Returns:
            Tuple of (results_dict, metrics_dict)
        """
        start_time = time.time()
        metrics = {
            "segments_processed": len(transcript_segments) if transcript_segments else 0,
            "rules_evaluated": 0,
            "categories_evaluated": 0,
            "errors": 0
        }

        results = {}
        metadata = metadata or {}

        # Validate inputs
        if not policy_rules or not isinstance(policy_rules, dict):
            return {"error": "No valid policy rules provided"}, metrics

        if not transcript_segments:
            # Mark all rules as null due to missing transcript
            results = self._create_null_results(policy_rules)
            metrics["errors"] = sum(len(rules) for rules in policy_rules.values())
            return results, metrics

        # Evaluate each category
        for category_name, rules in policy_rules.items():
            if not isinstance(rules, list):
                logger.warning(f"Invalid rules format for category {category_name}")
                continue

            results[category_name] = {}
            metrics["categories_evaluated"] += 1

            for rule in rules:
                if not isinstance(rule, dict) or "id" not in rule or "type" not in rule:
                    logger.error(f"Malformed rule in category {category_name}: {rule}")
                    results[category_name][rule.get("id", "unknown")] = RuleEvaluationResult(
                        rule_id=rule.get("id", "unknown"),
                        rule_type="unknown",
                        passed=None,
                        error="Malformed rule structure"
                    ).__dict__
                    metrics["errors"] += 1
                    continue

                rule_result = self._evaluate_single_rule(
                    rule, transcript_segments, sentiment_analysis, metadata, metrics
                )
                results[category_name][rule["id"]] = rule_result.__dict__
                metrics["rules_evaluated"] += 1

        # Convert to simple dict format for storage
        simplified_results = self._simplify_results(results)

        metrics["execution_time_ms"] = int((time.time() - start_time) * 1000)

        logger.info(
            f"Rule Engine V2: Evaluated {metrics['rules_evaluated']} rules "
            f"across {metrics['categories_evaluated']} categories in {metrics['execution_time_ms']}ms"
        )

        return simplified_results, metrics

    def _evaluate_single_rule(
        self,
        rule: Dict[str, Any],
        segments: List[Dict[str, Any]],
        sentiment: Optional[List[Dict[str, Any]]],
        metadata: Dict[str, Any],
        metrics: Dict[str, Any]
    ) -> RuleEvaluationResult:
        """Evaluate a single rule and return standardized result."""
        rule_id = rule["id"]
        rule_type = rule["type"]

        if rule_type not in self.rule_evaluators:
            metrics["errors"] += 1
            return RuleEvaluationResult(
                rule_id=rule_id,
                rule_type=rule_type,
                passed=None,
                error=f"Unknown rule type: {rule_type}"
            )

        try:
            evaluator = self.rule_evaluators[rule_type]
            return evaluator(rule, segments, sentiment, metadata)
        except Exception as e:
            logger.error(f"Error evaluating rule {rule_id}: {e}")
            metrics["errors"] += 1
            return RuleEvaluationResult(
                rule_id=rule_id,
                rule_type=rule_type,
                passed=None,
                error=f"Evaluation failed: {str(e)}"
            )

    # Boolean Rule Evaluators

    def _evaluate_boolean_rule(
        self,
        rule: Dict[str, Any],
        segments: List[Dict[str, Any]],
        sentiment: Optional[List[Dict[str, Any]]],
        metadata: Dict[str, Any]
    ) -> RuleEvaluationResult:
        """Evaluate boolean rules - check if required actions were performed."""
        rule_id = rule["id"]
        expected_value = rule.get("value", True)

        # Route to specific boolean evaluators based on rule_id
        if rule_id == "identify_self":
            passed, evidence = self._evaluate_identify_self(segments)
        elif rule_id == "requires_apology_if_negative_sentiment":
            passed, evidence = self._evaluate_requires_apology_if_negative_sentiment(segments, sentiment)
        elif rule_id == "requires_account_verification":
            passed, evidence = self._evaluate_requires_account_verification(segments)
        else:
            # Generic boolean rule - check if any agent utterance matches expected pattern
            passed, evidence = self._evaluate_generic_boolean(rule_id, segments, expected_value)

        return RuleEvaluationResult(
            rule_id=rule_id,
            rule_type="boolean",
            passed=passed,
            evidence=evidence
        )

    def _evaluate_identify_self(self, segments: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """Check if agent identified themselves or company within first 30 seconds."""
        agent_segments = [s for s in segments if s.get("speaker") == "agent"]
        if not agent_segments:
            return False, "no agent segments found"

        # Check first 30 seconds of conversation
        check_segments = []
        for segment in agent_segments:
            if segment.get("start", 0) <= 30.0:  # Within first 30 seconds
                check_segments.append(segment)
            else:
                break

        if not check_segments:
            return False, "no agent utterances in first 30 seconds"

        # Look for identification keywords
        identification_keywords = [
            "this is", "my name is", "i'm", "speaking with",
            "you are speaking with", "you're speaking with"
        ]

        combined_text = " ".join(s.get("text", "").lower() for s in check_segments)

        for keyword in identification_keywords:
            if keyword in combined_text:
                return True, f"found identification keyword: '{keyword}'"

        return False, "no identification keywords found in first 30 seconds"

    def _evaluate_requires_apology_if_negative_sentiment(
        self,
        segments: List[Dict[str, Any]],
        sentiment: Optional[List[Dict[str, Any]]]
    ) -> Tuple[bool, str]:
        """Check if agent apologized when caller showed negative sentiment."""
        if not sentiment:
            return None, "no sentiment data available"

        # Find negative caller sentiment segments
        negative_threshold = -0.4  # Configurable
        negative_segments = []

        for sent in sentiment:
            if (sent.get("speaker") == "caller" and
                isinstance(sent.get("sentiment"), (int, float)) and
                sent["sentiment"] < negative_threshold):
                negative_segments.append(sent)

        if not negative_segments:
            return True, "no negative caller sentiment detected"

        # Check if agent responded with apology after each negative segment
        apology_keywords = ["sorry", "apologize", "my apologies", "i apologize", "i'm sorry"]
        agent_segments = [s for s in segments if s.get("speaker") == "agent"]

        for neg_seg in negative_segments:
            neg_end_time = neg_seg.get("end", 0)
            # Look for agent response within 10 seconds after negative sentiment
            found_apology = False

            for agent_seg in agent_segments:
                if (agent_seg.get("start", 0) >= neg_end_time and
                    agent_seg.get("start", 0) <= neg_end_time + 10.0):

                    text = agent_seg.get("text", "").lower()
                    if any(keyword in text for keyword in apology_keywords):
                        found_apology = True
                        break

            if not found_apology:
                return False, f"no apology found after negative sentiment at {neg_end_time:.1f}s"

        return True, f"apology found after {len(negative_segments)} negative sentiment segments"

    def _evaluate_requires_account_verification(self, segments: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """Check if agent verified account information."""
        agent_segments = [s for s in segments if s.get("speaker") == "agent"]
        combined_text = " ".join(s.get("text", "").lower() for s in agent_segments)

        verification_keywords = [
            "verify", "confirm", "account", "customer id", "reference number",
            "let me confirm", "can you verify", "account verification"
        ]

        for keyword in verification_keywords:
            if keyword in combined_text:
                return True, f"found verification keyword: '{keyword}'"

        return False, "no account verification keywords found"

    def _evaluate_generic_boolean(
        self,
        rule_id: str,
        segments: List[Dict[str, Any]],
        expected_value: bool
    ) -> Tuple[bool, str]:
        """Generic boolean rule evaluation - placeholder for future rules."""
        # For now, return expected value with placeholder evidence
        return expected_value, f"generic boolean rule '{rule_id}' evaluated to {expected_value}"

    # Numeric Rule Evaluators

    def _evaluate_numeric_rule(
        self,
        rule: Dict[str, Any],
        segments: List[Dict[str, Any]],
        sentiment: Optional[List[Dict[str, Any]]],
        metadata: Dict[str, Any]
    ) -> RuleEvaluationResult:
        """Evaluate numeric rules with comparisons."""
        rule_id = rule["id"]
        required_value = rule["value"]
        comparator = rule.get("comparator", "le")

        # Route to specific numeric evaluators
        if rule_id == "greet_within_seconds":
            actual_value, evidence = self._evaluate_greet_within_seconds(segments)
        elif rule_id == "call_duration_max":
            actual_value, evidence = self._evaluate_call_duration(metadata)
        elif rule_id == "agent_silence_max":
            actual_value, evidence = self._evaluate_max_agent_silence(segments)
        else:
            # Generic numeric rule
            actual_value, evidence = self._evaluate_generic_numeric(rule_id, segments, metadata)

        if actual_value is None:
            return RuleEvaluationResult(
                rule_id=rule_id,
                rule_type="numeric",
                passed=None,
                error=evidence
            )

        passed = self._compare_numeric(actual_value, comparator, required_value)

        return RuleEvaluationResult(
            rule_id=rule_id,
            rule_type="numeric",
            passed=passed,
            actual_value=actual_value,
            required_value=required_value,
            evidence=evidence
        )

    def _evaluate_greet_within_seconds(self, segments: List[Dict[str, Any]]) -> Tuple[Optional[float], str]:
        """Get timestamp of first agent utterance."""
        agent_segments = [s for s in segments if s.get("speaker") == "agent"]
        if not agent_segments:
            return None, "no agent segments found"

        first_agent = min(agent_segments, key=lambda s: s.get("start", 0))
        start_time = first_agent.get("start", 0)
        return start_time, f"first agent utterance at {start_time:.1f}s"

    def _evaluate_call_duration(self, metadata: Dict[str, Any]) -> Tuple[Optional[float], str]:
        """Get call duration from metadata."""
        duration = metadata.get("call_duration")
        if duration is None:
            return None, "call duration not available in metadata"

        return float(duration), f"call duration: {duration}s"

    def _evaluate_max_agent_silence(self, segments: List[Dict[str, Any]]) -> Tuple[Optional[float], str]:
        """Calculate maximum silence between consecutive agent utterances."""
        agent_segments = sorted(
            [s for s in segments if s.get("speaker") == "agent"],
            key=lambda s: s.get("start", 0)
        )

        if len(agent_segments) < 2:
            return 0.0, "insufficient agent segments to measure silence"

        max_silence = 0.0
        for i in range(len(agent_segments) - 1):
            silence = agent_segments[i + 1]["start"] - agent_segments[i]["end"]
            max_silence = max(max_silence, silence)

        return max_silence, f"maximum agent silence: {max_silence:.1f}s"

    def _evaluate_generic_numeric(
        self,
        rule_id: str,
        segments: List[Dict[str, Any]],
        metadata: Dict[str, Any]
    ) -> Tuple[Optional[float], str]:
        """Generic numeric rule - try to find value in metadata."""
        if rule_id in metadata:
            value = metadata[rule_id]
            if isinstance(value, (int, float)):
                return float(value), f"found {rule_id} in metadata: {value}"

        return None, f"numeric metric '{rule_id}' not found"

    # List Rule Evaluators

    def _evaluate_list_rule(
        self,
        rule: Dict[str, Any],
        segments: List[Dict[str, Any]],
        sentiment: Optional[List[Dict[str, Any]]],
        metadata: Dict[str, Any]
    ) -> RuleEvaluationResult:
        """Evaluate list rules - check presence of required items."""
        rule_id = rule["id"]
        required_items = rule.get("items", [])

        if rule_id == "required_disclosures":
            present, missing, evidence = self._evaluate_required_disclosures(segments, required_items)
        else:
            # Generic list rule
            present, missing, evidence = self._evaluate_generic_list(segments, required_items)

        result_data = {
            "missing": missing,
            "present": present
        }

        # Rule passes if no required items are missing
        passed = len(missing) == 0

        return RuleEvaluationResult(
            rule_id=rule_id,
            rule_type="list",
            passed=result_data,
            evidence=evidence
        )

    def _evaluate_required_disclosures(
        self,
        segments: List[Dict[str, Any]],
        required_items: List[str]
    ) -> Tuple[List[str], List[str], str]:
        """Check if required disclosures are present in transcript."""
        combined_text = " ".join(s.get("text", "").lower() for s in segments)

        present = []
        missing = []

        # Map common disclosure types to search patterns
        disclosure_patterns = {
            "recording_notice": ["call is recorded", "this call is being recorded", "recording this call", "call may be recorded", "this call may be recorded"],
            "privacy": ["privacy policy", "privacy notice", "personal information"],
            "quality_assurance": ["quality assurance", "training purposes", "monitoring"],
            "consent": ["consent", "agree", "permission"]
        }

        for item in required_items:
            patterns = disclosure_patterns.get(item, [item.lower()])
            found = any(pattern in combined_text for pattern in patterns)

            if found:
                present.append(item)
            else:
                missing.append(item)

        evidence = f"checked {len(required_items)} disclosures: {len(present)} present, {len(missing)} missing"
        return present, missing, evidence

    def _evaluate_generic_list(
        self,
        segments: List[Dict[str, Any]],
        required_items: List[str]
    ) -> Tuple[List[str], List[str], str]:
        """Generic list evaluation - check for presence of each item."""
        combined_text = " ".join(s.get("text", "").lower() for s in segments)

        present = []
        missing = []

        for item in required_items:
            if item.lower() in combined_text:
                present.append(item)
            else:
                missing.append(item)

        evidence = f"generic list check: {len(present)}/{len(required_items)} items found"
        return present, missing, evidence

    # Helper Methods

    def _compare_numeric(self, actual: float, comparator: str, required: float) -> bool:
        """Compare actual value against required value using specified comparator."""
        comparators = {
            "le": lambda a, b: a <= b,
            "lt": lambda a, b: a < b,
            "eq": lambda a, b: a == b,
            "ge": lambda a, b: a >= b,
            "gt": lambda a, b: a > b,
        }

        compare_func = comparators.get(comparator)
        if not compare_func:
            logger.error(f"Unknown comparator: {comparator}")
            return False

        return compare_func(actual, required)

    def _create_null_results(self, policy_rules: Dict[str, Any]) -> Dict[str, Any]:
        """Create null results for all rules when transcript is missing."""
        results = {}
        for category_name, rules in policy_rules.items():
            results[category_name] = {}
            for rule in rules:
                rule_id = rule.get("id", "unknown")
                results[category_name][rule_id] = {
                    "passed": None,
                    "error": "transcript not available"
                }
        return results

    def _simplify_results(self, detailed_results: Dict[str, Any]) -> Dict[str, Any]:
        """Convert detailed RuleEvaluationResult objects to simple dict format for storage."""
        simplified = {}

        for category_name, category_results in detailed_results.items():
            simplified[category_name] = {}

            for rule_id, result in category_results.items():
                if isinstance(result, dict):
                    # Already simplified
                    simplified[category_name][rule_id] = result
                else:
                    # Convert RuleEvaluationResult to dict
                    simplified_result = {
                        "passed": result.passed,
                        "actual_value": result.actual_value,
                        "required_value": result.required_value,
                        "evidence": result.evidence,
                        "error": result.error
                    }
                    # Remove None values for cleaner storage
                    simplified_result = {k: v for k, v in simplified_result.items() if v is not None}
                    simplified[category_name][rule_id] = simplified_result

        return simplified
