"""
Rule Engine V2 Service
Phase 3: Policy-Based Deterministic Evaluation

Loads rules dynamically from policy_rules JSONB and supports all rule types:
- Timing rules
- Phrase rules (required/forbidden)
- Boolean rules
- Conditional rules
- Multi-step rules
- Tone-based rules
- Resolution rules
"""

from typing import List, Dict, Any, Optional
import logging
import re
from datetime import datetime

from app.schemas.policy_rules import (
    PolicyRulesSchema,
    RuleType,
    Severity,
    BooleanRule,
    NumericRule,
    PhraseRule,
    ListRule,
    ConditionalRule,
    MultiStepRule,
    ToneBasedRule,
    ResolutionRule,
    PolicyRule
)

logger = logging.getLogger(__name__)


class RuleEngineV2:
    """
    Phase 3: Rule Engine V2 for deterministic policy rule evaluation.
    Loads rules from policy_rules JSONB and executes them deterministically.
    """

    def __init__(self, policy_rules: Optional[Dict[str, Any]] = None):
        """
        Initialize rule engine with policy rules.
        
        Args:
            policy_rules: PolicyRulesSchema dict or None to use hardcoded fallback
        """
        self.policy_rules = None
        self.rules_by_category = {}
        
        if policy_rules:
            try:
                validated = PolicyRulesSchema(**policy_rules)
                self.policy_rules = validated
                self._index_rules_by_category()
            except Exception as e:
                logger.warning(f"Failed to load policy rules, using fallback: {e}")
                self._load_fallback_rules()
        else:
            self._load_fallback_rules()

    def _load_fallback_rules(self):
        """Load fallback hardcoded rules for backward compatibility."""
        logger.info("Using fallback hardcoded rules")
        # Keep minimal fallback for backward compatibility
        self.rules_by_category = {
            "Professionalism": [],
            "Empathy": [],
            "Resolution": []
        }

    def _index_rules_by_category(self):
        """Index rules by category for efficient lookup."""
        if not self.policy_rules:
            return
        
        self.rules_by_category = {}
        for category, rules_list in self.policy_rules.rules.items():
            # Convert dict rules to Pydantic models (rules_list may already be Pydantic models)
            converted_rules = []
            for rule_item in rules_list:
                try:
                    # Check if already a Pydantic model
                    if hasattr(rule_item, 'type') and hasattr(rule_item, 'id'):
                        converted_rules.append(rule_item)
                        continue
                    
                    # Convert from dict
                    rule_dict = rule_item if isinstance(rule_item, dict) else rule_item.dict() if hasattr(rule_item, 'dict') else {}
                    rule_type = rule_dict.get("type") if isinstance(rule_dict, dict) else getattr(rule_item, 'type', None)
                    
                    if rule_type == RuleType.BOOLEAN.value or rule_type == RuleType.BOOLEAN:
                        converted_rules.append(BooleanRule(**rule_dict))
                    elif rule_type == RuleType.NUMERIC.value or rule_type == RuleType.NUMERIC:
                        converted_rules.append(NumericRule(**rule_dict))
                    elif rule_type == RuleType.PHRASE.value or rule_type == RuleType.PHRASE:
                        converted_rules.append(PhraseRule(**rule_dict))
                    elif rule_type == RuleType.LIST.value or rule_type == RuleType.LIST:
                        converted_rules.append(ListRule(**rule_dict))
                    elif rule_type == RuleType.CONDITIONAL.value or rule_type == RuleType.CONDITIONAL:
                        converted_rules.append(ConditionalRule(**rule_dict))
                    elif rule_type == RuleType.MULTI_STEP.value or rule_type == RuleType.MULTI_STEP:
                        converted_rules.append(MultiStepRule(**rule_dict))
                    elif rule_type == RuleType.TONE_BASED.value or rule_type == RuleType.TONE_BASED:
                        converted_rules.append(ToneBasedRule(**rule_dict))
                    elif rule_type == RuleType.RESOLUTION.value or rule_type == RuleType.RESOLUTION:
                        converted_rules.append(ResolutionRule(**rule_dict))
                    else:
                        logger.warning(f"Unknown rule type: {rule_type}")
                except Exception as e:
                    rule_id = rule_dict.get('id', 'unknown') if isinstance(rule_dict, dict) else getattr(rule_item, 'id', 'unknown')
                    logger.error(f"Failed to convert rule {rule_id}: {e}")
            self.rules_by_category[category] = converted_rules

    def evaluate_rules(
        self,
        transcript_segments: List[Dict[str, Any]],
        sentiment_analysis: Optional[List[Dict[str, Any]]] = None,
        policy_template_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate all rules against transcript and return standardized results.
        
        Args:
            transcript_segments: Diarized transcript segments with speaker, text, start, end
            sentiment_analysis: Optional sentiment analysis data
            policy_template_id: Optional policy template ID for logging
            
        Returns:
            Dictionary with structure:
            {
                "category_name": {
                    "rule_id": {
                        "passed": bool,
                        "severity": str,
                        "evidence": List[Dict],
                        "category": str
                    }
                },
                "summary": {
                    "total_rules": int,
                    "passed": int,
                    "failed": int,
                    "violations_by_category": Dict[str, int]
                }
            }
        """
        logger.info(f"Evaluating rules - segments: {len(transcript_segments)}, categories: {len(self.rules_by_category)}")
        
        results = {}
        summary = {
            "total_rules": 0,
            "passed": 0,
            "failed": 0,
            "violations_by_category": {}
        }
        
        # Evaluate rules by category
        for category_name, rules in self.rules_by_category.items():
            category_results = {}
            
            for rule in rules:
                if not rule.enabled:
                    continue
                
                summary["total_rules"] += 1
                
                # Evaluate rule based on type
                rule_result = self._evaluate_rule_by_type(
                    rule=rule,
                    transcript_segments=transcript_segments,
                    sentiment_analysis=sentiment_analysis
                )
                
                category_results[rule.id] = rule_result
                
                if rule_result["passed"]:
                    summary["passed"] += 1
                else:
                    summary["failed"] += 1
                    summary["violations_by_category"][category_name] = \
                        summary["violations_by_category"].get(category_name, 0) + 1
            
            if category_results:
                results[category_name] = category_results
        
        logger.info(f"Rule evaluation completed: {summary['passed']}/{summary['total_rules']} passed")
        
        return {
            **results,
            "summary": summary
        }

    def _evaluate_rule_by_type(
        self,
        rule: PolicyRule,
        transcript_segments: List[Dict[str, Any]],
        sentiment_analysis: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Evaluate a rule based on its type."""
        rule_type = rule.type
        
        if rule_type == RuleType.BOOLEAN:
            return self._evaluate_boolean_rule(rule, transcript_segments, sentiment_analysis)
        elif rule_type == RuleType.NUMERIC:
            return self._evaluate_numeric_rule(rule, transcript_segments, sentiment_analysis)
        elif rule_type == RuleType.PHRASE:
            return self._evaluate_phrase_rule(rule, transcript_segments)
        elif rule_type == RuleType.LIST:
            return self._evaluate_list_rule(rule, transcript_segments)
        elif rule_type == RuleType.CONDITIONAL:
            return self._evaluate_conditional_rule(rule, transcript_segments, sentiment_analysis)
        elif rule_type == RuleType.MULTI_STEP:
            return self._evaluate_multi_step_rule(rule, transcript_segments)
        elif rule_type == RuleType.TONE_BASED:
            return self._evaluate_tone_rule(rule, transcript_segments, sentiment_analysis)
        elif rule_type == RuleType.RESOLUTION:
            return self._evaluate_resolution_rule(rule, transcript_segments)
        else:
            logger.warning(f"Unknown rule type: {rule_type}")
            return {
                "passed": True,
                "severity": rule.severity.value,
                "evidence": [],
                "category": rule.category
            }

    def _evaluate_boolean_rule(
        self,
        rule: BooleanRule,
        segments: List[Dict[str, Any]],
        sentiment_analysis: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Evaluate boolean rule (presence/absence of behavior)."""
        evidence = []
        
        # Check agent segments
        agent_segments = [s for s in segments if s.get("speaker") == "agent"]
        
        # Check for evidence patterns
        found = False
        for segment in agent_segments:
            text = segment.get("text", "").lower()
            for pattern in rule.evidence_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    found = True
                    evidence.append({
                        "speaker": "agent",
                        "text": segment.get("text", ""),
                        "start": segment.get("start", 0),
                        "end": segment.get("end", 0)
                    })
                    break
        
        # Check time window if specified
        if rule.time_window_seconds and evidence:
            first_evidence = min(evidence, key=lambda x: x.get("start", 0))
            if first_evidence.get("start", 0) > rule.time_window_seconds:
                found = False
                evidence = [{
                    "speaker": "system",
                    "text": f"Behavior found but outside {rule.time_window_seconds}s window",
                    "start": first_evidence.get("start", 0)
                }]
        
        # Rule passes if required behavior is found, or forbidden behavior is not found
        passed = (rule.required and found) or (not rule.required and not found)
        
        return {
            "passed": passed,
            "severity": rule.severity.value,
            "evidence": evidence if not passed else [],
            "category": rule.category
        }

    def _evaluate_numeric_rule(
        self,
        rule: NumericRule,
        segments: List[Dict[str, Any]],
        sentiment_analysis: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Evaluate numeric rule (threshold comparison)."""
        evidence = []
        
        # Get measurement value based on measurement_field
        measurement_value = self._get_measurement_value(
            rule.measurement_field,
            segments,
            sentiment_analysis
        )
        
        if measurement_value is None:
            # Can't measure - rule fails
            return {
                "passed": False,
                "severity": rule.severity.value,
                "evidence": [{"speaker": "system", "text": f"Could not measure {rule.measurement_field}"}],
                "category": rule.category,
                "value": None
            }
        
        # Compare based on comparator
        passed = self._compare_numeric(measurement_value, rule.comparator, rule.value)
        
        if not passed:
            evidence.append({
                "speaker": "system",
                "text": f"{rule.measurement_field}={measurement_value}{rule.unit}, required {rule.comparator} {rule.value}{rule.unit}",
                "start": 0
            })
        
        return {
            "passed": passed,
            "severity": rule.severity.value,
            "evidence": evidence,
            "category": rule.category,
            "value": measurement_value
        }

    def _evaluate_phrase_rule(
        self,
        rule: PhraseRule,
        segments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Evaluate phrase rule (required or forbidden phrases)."""
        evidence = []
        found_phrases = []
        
        # Check all segments
        for segment in segments:
            text = segment.get("text", "")
            check_text = text.lower() if not rule.case_sensitive else text
            
            for phrase in rule.phrases:
                check_phrase = phrase.lower() if not rule.case_sensitive else phrase
                
                if rule.fuzzy_match:
                    # Simple fuzzy match (contains)
                    if check_phrase in check_text:
                        found_phrases.append(phrase)
                        evidence.append({
                            "speaker": segment.get("speaker", "unknown"),
                            "text": segment.get("text", ""),
                            "start": segment.get("start", 0),
                            "end": segment.get("end", 0),
                            "matched_phrase": phrase
                        })
                else:
                    # Exact match
                    if check_phrase in check_text:
                        found_phrases.append(phrase)
                        evidence.append({
                            "speaker": segment.get("speaker", "unknown"),
                            "text": segment.get("text", ""),
                            "start": segment.get("start", 0),
                            "end": segment.get("end", 0),
                            "matched_phrase": phrase
                        })
        
        # Rule passes if required phrases found, or forbidden phrases not found
        passed = (rule.required and len(found_phrases) > 0) or (not rule.required and len(found_phrases) == 0)
        
        return {
            "passed": passed,
            "severity": rule.severity.value,
            "evidence": evidence if not passed else [],
            "category": rule.category,
            "found_phrases": found_phrases
        }

    def _evaluate_list_rule(
        self,
        rule: ListRule,
        segments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Evaluate list rule (must contain items from list)."""
        evidence = []
        found_items = []
        
        # Check all segments for required items
        all_text = " ".join([s.get("text", "") for s in segments]).lower()
        
        for item in rule.required_items:
            if item.lower() in all_text:
                found_items.append(item)
        
        # Check if minimum required items found
        min_met = len(found_items) >= rule.min_required
        
        # Check if all required (if all_required flag is set)
        all_met = not rule.all_required or len(found_items) == len(rule.required_items)
        
        passed = min_met and all_met
        
        if not passed:
            missing = set(rule.required_items) - set(found_items)
            evidence.append({
                "speaker": "system",
                "text": f"Missing required items: {', '.join(missing)}",
                "start": 0
            })
        
        return {
            "passed": passed,
            "severity": rule.severity.value,
            "evidence": evidence,
            "category": rule.category,
            "found_items": found_items
        }

    def _evaluate_conditional_rule(
        self,
        rule: ConditionalRule,
        segments: List[Dict[str, Any]],
        sentiment_analysis: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Evaluate conditional rule (if-then logic)."""
        # Evaluate condition
        condition_met = self._evaluate_condition(
            rule.condition,
            segments,
            sentiment_analysis
        )
        
        if not condition_met:
            # Condition not met - rule passes (no requirement)
            return {
                "passed": True,
                "severity": rule.severity.value,
                "evidence": [],
                "category": rule.category
            }
        
        # Condition met - evaluate then_rule
        # For now, treat then_rule as a nested rule definition
        # This is simplified - full implementation would recursively evaluate
        logger.warning("Conditional rule evaluation simplified - full nested evaluation not implemented")
        
        return {
            "passed": True,  # Simplified - assume passes if condition met
            "severity": rule.severity.value,
            "evidence": [],
            "category": rule.category
        }

    def _evaluate_multi_step_rule(
        self,
        rule: MultiStepRule,
        segments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Evaluate multi-step rule (ordered checklist)."""
        evidence = []
        step_found = [False] * len(rule.steps)
        
        # Check each step
        for step_idx, step in enumerate(rule.steps):
            step_desc = step.get("description", "")
            step_patterns = step.get("evidence_patterns", [])
            
            # Find step in segments
            for segment in segments:
                text = segment.get("text", "").lower()
                
                # Check if step patterns match
                if step_patterns:
                    for pattern in step_patterns:
                        if re.search(pattern, text, re.IGNORECASE):
                            step_found[step_idx] = True
                            evidence.append({
                                "speaker": segment.get("speaker", "unknown"),
                                "text": segment.get("text", ""),
                                "start": segment.get("start", 0),
                                "step": step_idx + 1,
                                "step_description": step_desc
                            })
                            break
                
                if step_found[step_idx]:
                    break
        
        # Check order if strict_order is True
        if rule.strict_order:
            # Verify steps occur in order
            last_found_idx = -1
            for idx, found in enumerate(step_found):
                if found:
                    if idx < last_found_idx:
                        # Step found out of order
                        return {
                            "passed": False,
                            "severity": rule.severity.value,
                            "evidence": evidence + [{
                                "speaker": "system",
                                "text": f"Step {idx + 1} found out of order",
                                "start": 0
                            }],
                            "category": rule.category
                        }
                    last_found_idx = idx
        
        # Check if all steps found
        all_steps_found = all(step_found)
        
        return {
            "passed": all_steps_found,
            "severity": rule.severity.value,
            "evidence": evidence if not all_steps_found else [],
            "category": rule.category,
            "steps_found": step_found
        }

    def _evaluate_tone_rule(
        self,
        rule: ToneBasedRule,
        segments: List[Dict[str, Any]],
        sentiment_analysis: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Evaluate tone-based rule (sentiment/tone mismatches)."""
        evidence = []
        
        if not sentiment_analysis:
            # No sentiment data - rule passes (can't evaluate)
            return {
                "passed": True,
                "severity": rule.severity.value,
                "evidence": [],
                "category": rule.category
            }
        
        # Check for tone mismatches
        mismatches = []
        
        # Simplified tone mismatch detection
        # Full implementation would compare against baseline and check specific phrases
        if rule.required_phrases_with_tone:
            for segment in segments:
                if segment.get("speaker") == "agent":
                    text = segment.get("text", "").lower()
                    for phrase in rule.required_phrases_with_tone:
                        if phrase.lower() in text:
                            # Check if tone matches
                            # Simplified - would need full tone analysis
                            pass
        
        return {
            "passed": len(mismatches) == 0,
            "severity": rule.severity.value,
            "evidence": mismatches,
            "category": rule.category
        }

    def _evaluate_resolution_rule(
        self,
        rule: ResolutionRule,
        segments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Evaluate resolution rule (issue resolution detection)."""
        evidence = []
        
        # Check for resolution markers
        all_text = " ".join([s.get("text", "") for s in segments]).lower()
        resolution_found = False
        
        if rule.resolution_markers:
            for marker in rule.resolution_markers:
                if marker.lower() in all_text:
                    resolution_found = True
                    break
        
        # Check if resolution required
        if rule.must_resolve and not resolution_found:
            evidence.append({
                "speaker": "system",
                "text": "No resolution detected",
                "start": 0
            })
        
        # Check for next steps documentation if unresolved
        if rule.must_document_next_steps and not resolution_found:
            next_steps_found = False
            if rule.next_steps_markers:
                for marker in rule.next_steps_markers:
                    if marker.lower() in all_text:
                        next_steps_found = True
                        break
            
            if not next_steps_found:
                evidence.append({
                    "speaker": "system",
                    "text": "Issue unresolved but no next steps documented",
                    "start": 0
                })
        
        passed = len(evidence) == 0
        
        return {
            "passed": passed,
            "severity": rule.severity.value,
            "evidence": evidence,
            "category": rule.category,
            "resolution_detected": resolution_found
        }

    def _get_measurement_value(
        self,
        measurement_field: str,
        segments: List[Dict[str, Any]],
        sentiment_analysis: Optional[List[Dict[str, Any]]]
    ) -> Optional[float]:
        """Get measurement value for numeric rules."""
        # Common measurement fields
        if measurement_field == "greeting_time":
            agent_segments = [s for s in segments if s.get("speaker") == "agent"]
            if agent_segments:
                first_agent = min(agent_segments, key=lambda x: x.get("start", 0))
                return first_agent.get("start", 0)
        
        elif measurement_field == "silence_duration":
            if len(segments) < 2:
                return 0.0
            max_silence = 0.0
            sorted_segments = sorted(segments, key=lambda x: x.get("start", 0))
            for i in range(len(sorted_segments) - 1):
                silence = sorted_segments[i + 1].get("start", 0) - sorted_segments[i].get("end", 0)
                max_silence = max(max_silence, silence)
            return max_silence
        
        elif measurement_field == "response_time":
            # Average response time between caller and agent
            response_times = []
            for i in range(len(segments) - 1):
                if segments[i].get("speaker") == "caller" and segments[i + 1].get("speaker") == "agent":
                    response_time = segments[i + 1].get("start", 0) - segments[i].get("end", 0)
                    response_times.append(response_time)
            if response_times:
                return sum(response_times) / len(response_times)
            return 0.0
        
        return None

    def _compare_numeric(self, value: float, comparator: str, threshold: float) -> bool:
        """Compare numeric value with threshold."""
        if comparator == "le":
            return value <= threshold
        elif comparator == "lt":
            return value < threshold
        elif comparator == "ge":
            return value >= threshold
        elif comparator == "gt":
            return value > threshold
        elif comparator == "eq":
            return abs(value - threshold) < 0.01  # Float comparison
        return False

    def _evaluate_condition(
        self,
        condition: Dict[str, Any],
        segments: List[Dict[str, Any]],
        sentiment_analysis: Optional[List[Dict[str, Any]]]
    ) -> bool:
        """Evaluate condition for conditional rules."""
        field = condition.get("field")
        operator = condition.get("operator")
        value = condition.get("value")
        
        # Simplified condition evaluation
        # Full implementation would support more field types and operators
        if field == "caller_sentiment":
            if sentiment_analysis:
                # Check if any caller segment has negative sentiment
                for sent in sentiment_analysis:
                    if sent.get("speaker") == "caller":
                        sentiment_obj = sent.get("sentiment", {})
                        if isinstance(sentiment_obj, dict):
                            sentiment_value = sentiment_obj.get("sentiment")
                        else:
                            sentiment_value = sentiment_obj
                        
                        if operator == "le" and sentiment_value == "negative":
                            return True
        
        return False
