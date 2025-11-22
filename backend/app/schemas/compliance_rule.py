"""
Phase 2: ComplianceRule Schemas
Pydantic schemas for ComplianceRule CRUD operations with type-specific param schemas.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from app.models.compliance_rule import RuleType, Severity


# Rule type-specific param schemas per Phase 2 spec

class RequiredPhraseParams(BaseModel):
    phrases: List[str] = Field(..., min_items=1)
    match_type: Literal["exact", "contains", "regex"] = "contains"
    case_sensitive: bool = False
    scope: Literal["stage", "call"] = "call"
    allowed_variants: Optional[List[str]] = []


class ForbiddenPhraseParams(BaseModel):
    phrases: List[str] = Field(..., min_items=1)
    match_type: Literal["contains", "regex"] = "contains"
    case_sensitive: bool = False
    scope: Literal["stage", "call"] = "call"


class SequenceRuleParams(BaseModel):
    before_step_id: str
    after_step_id: str
    allow_equal_timestamps: bool = False
    message_on_violation: Optional[str] = None


class TimingRuleParams(BaseModel):
    target: Literal["step", "phrase"]
    target_id_or_phrase: str
    within_seconds: float = Field(..., gt=0)
    reference: Literal["call_start", "previous_step"] = "call_start"
    scope_stage_id: Optional[str] = None


class VerificationRuleParams(BaseModel):
    verification_step_id: str
    required_question_count: int = Field(..., ge=1)
    must_complete_before_step_id: str
    allow_partial: bool = False


class ConditionalRuleCondition(BaseModel):
    type: Literal["sentiment", "phrase_mentioned", "metadata_flag"]
    operator: Literal["equals", "contains"]
    value: str


class ConditionalRuleAction(BaseModel):
    action_type: Literal["step_completed", "phrase_spoken"]
    step_id: Optional[str] = None
    phrase: Optional[str] = None


class ConditionalRuleParams(BaseModel):
    condition: ConditionalRuleCondition
    required_actions: List[ConditionalRuleAction] = Field(..., min_items=1)
    failure_severity: Literal["major", "minor"] = "major"
    scope_stage_id: Optional[str] = None


# Union type for params
ComplianceRuleParams = RequiredPhraseParams | ForbiddenPhraseParams | SequenceRuleParams | TimingRuleParams | VerificationRuleParams | ConditionalRuleParams


class ComplianceRuleCreate(BaseModel):
    flow_version_id: str
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    severity: Severity
    rule_type: RuleType
    applies_to_stages: Optional[List[str]] = []
    params: Dict[str, Any]
    active: bool = True


class ComplianceRuleUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = Field(None, min_length=1)
    severity: Optional[Severity] = None
    rule_type: Optional[RuleType] = None
    applies_to_stages: Optional[List[str]] = None
    params: Optional[Dict[str, Any]] = None
    active: Optional[bool] = None


class ComplianceRuleResponse(BaseModel):
    id: str
    flow_version_id: str
    title: str
    description: str
    severity: Severity
    rule_type: RuleType
    applies_to_stages: List[str]
    params: Dict[str, Any]
    active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RulePreviewResponse(BaseModel):
    preview: str  # Human-readable preview sentence


# Helper function to generate preview sentence
def generate_rule_preview(rule: ComplianceRuleResponse) -> str:
    """Generate human-readable preview sentence per Phase 2 spec"""
    if rule.rule_type == RuleType.required_phrase:
        params = rule.params
        phrases = params.get("phrases", [])
        scope = params.get("scope", "call")
        stage_text = f" within {', '.join(rule.applies_to_stages)} stage" if rule.applies_to_stages and scope == "stage" else ""
        return f"Required: agent must say one of {phrases}{stage_text}."
    
    elif rule.rule_type == RuleType.forbidden_phrase:
        params = rule.params
        phrases = params.get("phrases", [])
        return f"Forbidden: Agent must not say phrases matching {phrases} anywhere in call."
    
    elif rule.rule_type == RuleType.sequence_rule:
        params = rule.params
        before = params.get("before_step_id", "")
        after = params.get("after_step_id", "")
        return f"Agent must perform step {before} before step {after}."
    
    elif rule.rule_type == RuleType.timing_rule:
        params = rule.params
        target = params.get("target_id_or_phrase", "")
        seconds = params.get("within_seconds", 0)
        reference = params.get("reference", "call_start")
        ref_text = "call start" if reference == "call_start" else "previous step"
        return f"Agent must {target} within {seconds} seconds of {ref_text}."
    
    elif rule.rule_type == RuleType.verification_rule:
        params = rule.params
        count = params.get("required_question_count", 0)
        before = params.get("must_complete_before_step_id", "")
        return f"Agent must ask {count} KBA questions and record an answer before {before}."
    
    elif rule.rule_type == RuleType.conditional_rule:
        params = rule.params
        condition = params.get("condition", {})
        cond_type = condition.get("type", "")
        value = condition.get("value", "")
        return f"If {cond_type} is {value}, agent must perform required actions."
    
    return "Rule preview not available"

