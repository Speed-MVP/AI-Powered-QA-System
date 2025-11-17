"""
Policy Rules Schema Definition
Phase 1: Structured Rules Foundation

Defines the JSON schema for structured, machine-readable policy rules.
Supports multiple rule types: boolean, numeric, phrase, list, conditional, multi-step, tone-based, resolution.
"""

from typing import Dict, Any, List, Optional, Literal, Union
from pydantic import BaseModel, Field, validator
from enum import Enum


class RuleType(str, Enum):
    """Supported rule types."""
    BOOLEAN = "boolean"
    NUMERIC = "numeric"
    PHRASE = "phrase"
    LIST = "list"
    CONDITIONAL = "conditional"
    MULTI_STEP = "multi_step"
    TONE_BASED = "tone_based"
    RESOLUTION = "resolution"


class Severity(str, Enum):
    """Rule violation severity levels."""
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CRITICAL = "critical"


class RuleCategory(str, Enum):
    """Categories that rules can belong to."""
    PROFESSIONALISM = "Professionalism"
    EMPATHY = "Empathy"
    RESOLUTION = "Resolution"


# Base rule schema
class BaseRule(BaseModel):
    """Base rule structure shared by all rule types."""
    id: str = Field(..., description="Unique rule identifier")
    type: RuleType = Field(..., description="Rule type")
    category: str = Field(..., description="Category this rule belongs to (must match a category from the template's criteria)")
    severity: Severity = Field(..., description="Severity level if rule fails")
    enabled: bool = Field(True, description="Whether this rule is active")
    description: str = Field(..., description="Human-readable description of the rule")
    critical: bool = Field(False, description="If true, failure forces Unacceptable rubric level")
    
    @validator('category')
    def validate_category(cls, v):
        # Category must be a non-empty string - actual validation against template categories
        # happens at the service level when rules are applied to a specific template
        if not v or not isinstance(v, str) or not v.strip():
            raise ValueError("Category must be a non-empty string")
        return v.strip()


# Boolean rule: Must be true/false
class BooleanRule(BaseRule):
    """Rule that checks for presence/absence of a behavior."""
    type: Literal[RuleType.BOOLEAN] = RuleType.BOOLEAN
    required: bool = Field(..., description="Whether the behavior is required (true) or forbidden (false)")
    evidence_patterns: List[str] = Field(default_factory=list, description="Phrases/patterns that indicate the behavior")
    time_window_seconds: Optional[float] = Field(None, description="Optional time window to check within")


# Numeric rule: Threshold comparison
class NumericRule(BaseRule):
    """Rule that checks numeric thresholds (timing, counts, etc.)."""
    type: Literal[RuleType.NUMERIC] = RuleType.NUMERIC
    comparator: Literal["le", "lt", "ge", "gt", "eq"] = Field(..., description="Comparison operator: le=<=, lt=<, ge=>=, gt=>, eq==")
    value: float = Field(..., description="Numeric threshold value")
    unit: str = Field("seconds", description="Unit of measurement (seconds, minutes, count, etc.)")
    measurement_field: str = Field(..., description="What to measure (e.g., 'greeting_time', 'silence_duration')")


# Phrase rule: Required or forbidden phrases
class PhraseRule(BaseRule):
    """Rule that checks for required or forbidden phrases."""
    type: Literal[RuleType.PHRASE] = RuleType.PHRASE
    required: bool = Field(..., description="True if phrases are required, False if forbidden")
    phrases: List[str] = Field(..., min_items=1, description="List of phrases to check for")
    case_sensitive: bool = Field(False, description="Whether phrase matching is case-sensitive")
    fuzzy_match: bool = Field(False, description="Allow fuzzy matching (similar phrases)")


# List rule: Must contain items from a list
class ListRule(BaseRule):
    """Rule that requires certain items from a predefined list."""
    type: Literal[RuleType.LIST] = RuleType.LIST
    required_items: List[str] = Field(..., min_items=1, description="Items that must be present")
    min_required: int = Field(1, description="Minimum number of items required")
    all_required: bool = Field(False, description="If true, all items must be present")


# Conditional rule: If-then logic
class ConditionalRule(BaseRule):
    """Rule with conditional logic (if condition then requirement)."""
    type: Literal[RuleType.CONDITIONAL] = RuleType.CONDITIONAL
    condition: Dict[str, Any] = Field(..., description="Condition to check (e.g., {'field': 'caller_sentiment', 'operator': 'le', 'value': -0.4})")
    then_rule: Dict[str, Any] = Field(..., description="Rule to apply if condition is true (nested rule definition)")


# Multi-step rule: Ordered checklist
class MultiStepRule(BaseRule):
    """Rule that requires multiple steps in order."""
    type: Literal[RuleType.MULTI_STEP] = RuleType.MULTI_STEP
    steps: List[Dict[str, Any]] = Field(..., min_items=2, description="Ordered list of steps, each with description and evidence_patterns")
    strict_order: bool = Field(True, description="If true, steps must occur in exact order")
    allow_gaps: bool = Field(False, description="If true, allow gaps between steps")


# Tone-based rule: Sentiment/tone analysis
class ToneBasedRule(BaseRule):
    """Rule that checks tone/sentiment mismatches."""
    type: Literal[RuleType.TONE_BASED] = RuleType.TONE_BASED
    check_agent_tone: bool = Field(True, description="Check agent tone")
    check_caller_tone: bool = Field(False, description="Check caller tone")
    baseline_comparison: bool = Field(True, description="Compare against voice baseline")
    mismatch_threshold: float = Field(0.5, description="Threshold for detecting tone mismatch")
    required_phrases_with_tone: Optional[List[str]] = Field(None, description="If set, check tone when these phrases are used")


# Resolution rule: Issue resolution detection
class ResolutionRule(BaseRule):
    """Rule that checks for issue resolution."""
    type: Literal[RuleType.RESOLUTION] = RuleType.RESOLUTION
    must_resolve: bool = Field(True, description="If true, issue must be resolved")
    resolution_markers: List[str] = Field(default_factory=list, description="Phrases that indicate resolution")
    must_document_next_steps: bool = Field(False, description="If true, must document next steps if unresolved")
    next_steps_markers: List[str] = Field(default_factory=list, description="Phrases that indicate next steps documentation")


# Union type for all rule types
PolicyRule = Union[BooleanRule, NumericRule, PhraseRule, ListRule, ConditionalRule, MultiStepRule, ToneBasedRule, ResolutionRule]


class PolicyRulesSchema(BaseModel):
    """Complete policy rules schema."""
    version: int = Field(1, description="Schema version")
    rules: Dict[str, List[PolicyRule]] = Field(..., description="Rules grouped by category")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('rules')
    def validate_rules_by_category(cls, v):
        """Ensure rules are properly categorized."""
        # Categories are dynamic based on the template's criteria
        # Only validate that categories are non-empty strings
        for category in v.keys():
            if not category or not isinstance(category, str) or not category.strip():
                raise ValueError(f"Category must be a non-empty string, got: {category}")
        return v


def validate_rule(rule_dict: Dict[str, Any]) -> PolicyRule:
    """
    Validate a rule dictionary against the schema.
    
    Args:
        rule_dict: Dictionary containing rule definition
        
    Returns:
        Validated rule object
        
    Raises:
        ValueError: If rule is invalid
    """
    rule_type = rule_dict.get('type')
    
    if rule_type == RuleType.BOOLEAN:
        return BooleanRule(**rule_dict)
    elif rule_type == RuleType.NUMERIC:
        return NumericRule(**rule_dict)
    elif rule_type == RuleType.PHRASE:
        return PhraseRule(**rule_dict)
    elif rule_type == RuleType.LIST:
        return ListRule(**rule_dict)
    elif rule_type == RuleType.CONDITIONAL:
        return ConditionalRule(**rule_dict)
    elif rule_type == RuleType.MULTI_STEP:
        return MultiStepRule(**rule_dict)
    elif rule_type == RuleType.TONE_BASED:
        return ToneBasedRule(**rule_dict)
    elif rule_type == RuleType.RESOLUTION:
        return ResolutionRule(**rule_dict)
    else:
        raise ValueError(f"Unknown rule type: {rule_type}")


def validate_policy_rules(rules_dict: Dict[str, Any]) -> PolicyRulesSchema:
    """
    Validate a complete policy rules dictionary.
    
    Args:
        rules_dict: Dictionary containing policy rules structure
        
    Returns:
        Validated PolicyRulesSchema object
        
    Raises:
        ValueError: If rules are invalid
    """
    return PolicyRulesSchema(**rules_dict)


def detect_conflicting_rules(rules: Dict[str, List[PolicyRule]]) -> List[Dict[str, Any]]:
    """
    Detect conflicting rules (e.g., one requires escalation, another forbids it).
    
    Args:
        rules: Dictionary of rules by category
        
    Returns:
        List of conflict descriptions
    """
    conflicts = []
    
    # Flatten all rules
    all_rules = []
    for category_rules in rules.values():
        all_rules.extend(category_rules)
    
    # Check for contradictory phrase rules
    required_phrases = set()
    forbidden_phrases = set()
    
    for rule in all_rules:
        if isinstance(rule, PhraseRule):
            if rule.required:
                required_phrases.update(rule.phrases)
            else:
                forbidden_phrases.update(rule.phrases)
    
    # Find overlaps
    overlaps = required_phrases.intersection(forbidden_phrases)
    if overlaps:
        conflicts.append({
            "type": "contradictory_phrases",
            "description": f"Phrases both required and forbidden: {overlaps}",
            "phrases": list(overlaps)
        })
    
    return conflicts

