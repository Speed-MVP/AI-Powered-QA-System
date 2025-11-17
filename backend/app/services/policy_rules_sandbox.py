"""
Phase 5: Policy Rules Sandbox Evaluation Service
Allows testing policy rules against sample transcripts before publishing.
"""

import json
import logging
import time
from typing import Dict, Any, List, Optional, Tuple

from app.services.rule_engine_v2_deterministic import RuleEngineV2Deterministic
from app.services.deterministic_scorer import DeterministicScorer

logger = logging.getLogger(__name__)


class PolicyRulesSandboxService:
    """
    Service for sandbox evaluation of policy rules against sample transcripts.

    Provides safe testing environment for admins to preview rule effects
    before publishing changes.
    """

    def __init__(self):
        self.rule_engine = RuleEngineV2Deterministic()
        self.scorer = DeterministicScorer()
        self.sample_transcripts = self._load_sample_transcripts()

    def _load_sample_transcripts(self) -> List[Dict[str, Any]]:
        """Load sample transcripts for sandbox testing."""
        # In production, these would come from a database or fixtures
        return [
            {
                "id": "sample_1",
                "name": "Perfect Agent Call",
                "segments": [
                    {
                        "speaker": "agent",
                        "text": "Hello, thank you for calling Tech Support. This is Sarah speaking with you today.",
                        "start": 3.0,
                        "end": 10.0
                    },
                    {
                        "speaker": "caller",
                        "text": "Hi, I need help with my account.",
                        "start": 11.0,
                        "end": 15.0
                    },
                    {
                        "speaker": "agent",
                        "text": "I'd be happy to help. May I have your account number please?",
                        "start": 16.0,
                        "end": 22.0
                    }
                ],
                "sentiment": [
                    {"speaker": "caller", "sentiment": 0.3, "start": 11.0, "end": 15.0}
                ],
                "metadata": {"call_duration": 120.0}
            },
            {
                "id": "sample_2",
                "name": "Late Greeting + Angry Customer",
                "segments": [
                    {
                        "speaker": "agent",
                        "text": "Hi there!",  # Late greeting at 20 seconds
                        "start": 20.0,
                        "end": 22.0
                    },
                    {
                        "speaker": "caller",
                        "text": "This service is terrible! I've been waiting forever!",
                        "start": 23.0,
                        "end": 28.0
                    },
                    {
                        "speaker": "agent",
                        "text": "I apologize for the inconvenience. Let me assist you.",
                        "start": 29.0,
                        "end": 35.0
                    }
                ],
                "sentiment": [
                    {"speaker": "caller", "sentiment": -0.8, "start": 23.0, "end": 28.0}  # Very negative
                ],
                "metadata": {"call_duration": 180.0}
            },
            {
                "id": "sample_3",
                "name": "No Verification + Recording Disclosure",
                "segments": [
                    {
                        "speaker": "agent",
                        "text": "Hello, this is John. How can I help?",
                        "start": 5.0,
                        "end": 10.0
                    },
                    {
                        "speaker": "caller",
                        "text": "I need to update my payment method.",
                        "start": 11.0,
                        "end": 15.0
                    },
                    {
                        "speaker": "agent",
                        "text": "This call may be recorded for quality purposes. What would you like to update?",
                        "start": 16.0,
                        "end": 25.0
                    }
                ],
                "sentiment": [
                    {"speaker": "caller", "sentiment": 0.1, "start": 11.0, "end": 15.0}
                ],
                "metadata": {"call_duration": 90.0}
            }
        ]

    def evaluate_against_sample(
        self,
        policy_rules: Dict[str, Any],
        sample_id: Optional[str] = None,
        custom_transcript: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate policy rules against a sample transcript.

        Args:
            policy_rules: Rules to test
            sample_id: ID of built-in sample to use
            custom_transcript: Custom transcript to test against

        Returns:
            Evaluation results with policy_results and scoring preview
        """
        start_time = time.time()

        # Get the transcript to test against
        if custom_transcript:
            transcript_data = custom_transcript
        elif sample_id:
            transcript_data = next(
                (t for t in self.sample_transcripts if t["id"] == sample_id),
                self.sample_transcripts[0]  # Default to first sample
            )
        else:
            transcript_data = self.sample_transcripts[0]  # Default sample

        try:
            # Prepare data for rule engine
            transcript_segments = transcript_data["segments"]
            sentiment_analysis = transcript_data.get("sentiment", [])
            metadata = transcript_data.get("metadata", {})

            # Run rule engine evaluation
            rule_results, rule_metrics = self.rule_engine.evaluate_recording(
                policy_rules=policy_rules,
                transcript_segments=transcript_segments,
                sentiment_analysis=sentiment_analysis,
                metadata=metadata
            )

            # Calculate scoring preview (if we have rubric info)
            scoring_preview = self._calculate_scoring_preview(
                rule_results,
                policy_rules,
                transcript_data
            )

            execution_time_ms = int((time.time() - start_time) * 1000)

            return {
                "transcript_id": transcript_data["id"],
                "transcript_name": transcript_data["name"],
                "policy_results": rule_results,
                "rule_metrics": rule_metrics,
                "scoring_preview": scoring_preview,
                "execution_time_ms": execution_time_ms,
                "success": True
            }

        except Exception as e:
            logger.error(f"Sandbox evaluation failed: {e}")
            return {
                "transcript_id": transcript_data.get("id", "unknown"),
                "transcript_name": transcript_data.get("name", "Unknown"),
                "error": str(e),
                "success": False,
                "execution_time_ms": int((time.time() - start_time) * 1000)
            }

    def get_available_samples(self) -> List[Dict[str, Any]]:
        """
        Get list of available sample transcripts for testing.

        Returns:
            List of sample information
        """
        return [
            {
                "id": sample["id"],
                "name": sample["name"],
                "segment_count": len(sample["segments"]),
                "has_sentiment": len(sample.get("sentiment", [])) > 0,
                "call_duration": sample.get("metadata", {}).get("call_duration", 0)
            }
            for sample in self.sample_transcripts
        ]

    def _calculate_scoring_preview(
        self,
        rule_results: Dict[str, Any],
        policy_rules: Dict[str, Any],
        transcript_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate a preview of scoring effects for the tested rules.

        Args:
            rule_results: Results from rule engine
            policy_rules: The rules being tested
            transcript_data: Transcript metadata

        Returns:
            Preview of scoring effects
        """
        try:
            # This is a simplified preview - in production you'd need full rubric data
            preview = {
                "category_impacts": {},
                "rule_violations": [],
                "potential_penalties": []
            }

            # Analyze rule results for violations and potential impacts
            for category, rules in rule_results.items():
                violations = 0
                for rule_id, rule_result in rules.items():
                    if isinstance(rule_result, dict) and rule_result.get("passed") is False:
                        violations += 1
                        preview["rule_violations"].append({
                            "category": category,
                            "rule_id": rule_id,
                            "evidence": rule_result.get("evidence", "Rule violation detected")
                        })

                preview["category_impacts"][category] = {
                    "violations": violations,
                    "total_rules": len(rules),
                    "compliance_rate": (len(rules) - violations) / len(rules) if rules else 0
                }

            return preview

        except Exception as e:
            logger.warning(f"Could not calculate scoring preview: {e}")
            return {"error": f"Preview calculation failed: {str(e)}"}

    def validate_rules_safety(
        self,
        policy_rules: Dict[str, Any],
        max_samples: int = 3
    ) -> Dict[str, Any]:
        """
        Validate that rules don't cause runtime errors across multiple samples.

        Args:
            policy_rules: Rules to validate
            max_samples: Number of samples to test against

        Returns:
            Validation results
        """
        validation_results = {
            "tested_samples": 0,
            "successful_evaluations": 0,
            "errors": [],
            "warnings": [],
            "is_safe": True
        }

        samples_to_test = self.sample_transcripts[:max_samples]

        for sample in samples_to_test:
            validation_results["tested_samples"] += 1

            result = self.evaluate_against_sample(
                policy_rules=policy_rules,
                custom_transcript=sample
            )

            if result.get("success", False):
                validation_results["successful_evaluations"] += 1
            else:
                validation_results["errors"].append({
                    "sample": sample["name"],
                    "error": result.get("error", "Unknown error")
                })
                validation_results["is_safe"] = False

        # Check for potential issues
        if validation_results["successful_evaluations"] < validation_results["tested_samples"]:
            validation_results["warnings"].append(
                f"Rules failed on {validation_results['tested_samples'] - validation_results['successful_evaluations']} samples"
            )

        return validation_results
