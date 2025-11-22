"""
Phase 2: ComplianceRule Validator Service
Validates ComplianceRule structure and cross-references with FlowVersion.
"""

from typing import Tuple, List, Dict, Any
from app.models.compliance_rule import ComplianceRule, RuleType
from app.models.flow_version import FlowVersion
from app.models.flow_stage import FlowStage
from app.models.flow_step import FlowStep
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


class ComplianceRuleValidator:
    """Validates ComplianceRule per Phase 2 spec"""
    
    @staticmethod
    def validate_rule_params(rule_type: RuleType, params: Dict[str, Any], flow_version: FlowVersion) -> Tuple[bool, List[str]]:
        """
        Validate rule type-specific params.
        Returns (is_valid, list_of_errors)
        """
        errors = []
        
        if rule_type == RuleType.required_phrase:
            if "phrases" not in params or not isinstance(params["phrases"], list) or len(params["phrases"]) == 0:
                errors.append("required_phrase must have at least one phrase")
            else:
                for phrase in params["phrases"]:
                    if not isinstance(phrase, str) or not phrase.strip():
                        errors.append("All phrases must be non-empty strings")
            
            if params.get("match_type") not in ["exact", "contains", "regex"]:
                errors.append("match_type must be 'exact', 'contains', or 'regex'")
            
            if params.get("scope") not in ["stage", "call"]:
                errors.append("scope must be 'stage' or 'call'")
            
            # Validate applies_to_stages if scope is stage
            if params.get("scope") == "stage":
                applies_to = params.get("applies_to_stages", [])
                if not applies_to:
                    errors.append("applies_to_stages must be non-empty when scope is 'stage'")
                else:
                    for stage_id in applies_to:
                        if not any(s.id == stage_id for s in flow_version.stages):
                            errors.append(f"Stage ID {stage_id} does not exist in FlowVersion")
        
        elif rule_type == RuleType.forbidden_phrase:
            if "phrases" not in params or not isinstance(params["phrases"], list) or len(params["phrases"]) == 0:
                errors.append("forbidden_phrase must have at least one phrase")
            else:
                for phrase in params["phrases"]:
                    if not isinstance(phrase, str) or not phrase.strip():
                        errors.append("All phrases must be non-empty strings")
            
            if params.get("match_type") not in ["contains", "regex"]:
                errors.append("match_type must be 'contains' or 'regex'")
        
        elif rule_type == RuleType.sequence_rule:
            before_step_id = params.get("before_step_id")
            after_step_id = params.get("after_step_id")
            
            if not before_step_id or not after_step_id:
                errors.append("sequence_rule must have both before_step_id and after_step_id")
            else:
                # Validate step IDs exist
                all_step_ids = []
                for stage in flow_version.stages:
                    for step in stage.steps:
                        all_step_ids.append(step.id)
                
                if before_step_id not in all_step_ids:
                    errors.append(f"before_step_id {before_step_id} does not exist in FlowVersion")
                if after_step_id not in all_step_ids:
                    errors.append(f"after_step_id {after_step_id} does not exist in FlowVersion")
        
        elif rule_type == RuleType.timing_rule:
            within_seconds = params.get("within_seconds")
            if not within_seconds or within_seconds <= 0:
                errors.append("timing_rule must have positive within_seconds")
            
            if params.get("target") not in ["step", "phrase"]:
                errors.append("target must be 'step' or 'phrase'")
            
            if params.get("reference") not in ["call_start", "previous_step"]:
                errors.append("reference must be 'call_start' or 'previous_step'")
            
            # If target is step, validate step_id exists
            if params.get("target") == "step":
                target_id = params.get("target_id_or_phrase")
                all_step_ids = []
                for stage in flow_version.stages:
                    for step in stage.steps:
                        all_step_ids.append(step.id)
                
                if target_id not in all_step_ids:
                    errors.append(f"target step_id {target_id} does not exist in FlowVersion")
            
            # Validate scope_stage_id if provided
            if params.get("scope_stage_id"):
                if not any(s.id == params["scope_stage_id"] for s in flow_version.stages):
                    errors.append(f"scope_stage_id {params['scope_stage_id']} does not exist in FlowVersion")
        
        elif rule_type == RuleType.verification_rule:
            verification_step_id = params.get("verification_step_id")
            must_complete_before_step_id = params.get("must_complete_before_step_id")
            required_question_count = params.get("required_question_count")
            
            if not verification_step_id:
                errors.append("verification_rule must have verification_step_id")
            if not must_complete_before_step_id:
                errors.append("verification_rule must have must_complete_before_step_id")
            if not required_question_count or required_question_count < 1:
                errors.append("verification_rule must have required_question_count >= 1")
            
            # Validate step IDs exist
            all_step_ids = []
            for stage in flow_version.stages:
                for step in stage.steps:
                    all_step_ids.append(step.id)
            
            if verification_step_id and verification_step_id not in all_step_ids:
                errors.append(f"verification_step_id {verification_step_id} does not exist in FlowVersion")
            if must_complete_before_step_id and must_complete_before_step_id not in all_step_ids:
                errors.append(f"must_complete_before_step_id {must_complete_before_step_id} does not exist in FlowVersion")
        
        elif rule_type == RuleType.conditional_rule:
            condition = params.get("condition")
            required_actions = params.get("required_actions", [])
            
            if not condition:
                errors.append("conditional_rule must have condition")
            else:
                if condition.get("type") not in ["sentiment", "phrase_mentioned", "metadata_flag"]:
                    errors.append("condition.type must be 'sentiment', 'phrase_mentioned', or 'metadata_flag'")
            
            if not required_actions or len(required_actions) == 0:
                errors.append("conditional_rule must have at least one required_action")
            else:
                # Validate action step_ids if present
                all_step_ids = []
                for stage in flow_version.stages:
                    for step in stage.steps:
                        all_step_ids.append(step.id)
                
                for action in required_actions:
                    if action.get("action_type") == "step_completed":
                        step_id = action.get("step_id")
                        if step_id and step_id not in all_step_ids:
                            errors.append(f"Action step_id {step_id} does not exist in FlowVersion")
            
            # Validate scope_stage_id if provided
            if params.get("scope_stage_id"):
                if not any(s.id == params["scope_stage_id"] for s in flow_version.stages):
                    errors.append(f"scope_stage_id {params['scope_stage_id']} does not exist in FlowVersion")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_applies_to_stages(applies_to_stages: List[str], flow_version: FlowVersion) -> Tuple[bool, List[str]]:
        """Validate that all stage IDs in applies_to_stages exist"""
        errors = []
        
        if not applies_to_stages:
            return True, []  # Empty list is valid (means whole call)
        
        valid_stage_ids = {s.id for s in flow_version.stages}
        for stage_id in applies_to_stages:
            if stage_id not in valid_stage_ids:
                errors.append(f"Stage ID {stage_id} does not exist in FlowVersion")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def check_forbidden_required_conflict(
        rule: ComplianceRule,
        existing_rules: List[ComplianceRule],
        flow_version: FlowVersion
    ) -> Tuple[bool, str]:
        """
        Check if a forbidden_phrase conflicts with a required_phrase for the same stage.
        Returns (has_conflict, error_message)
        """
        if rule.rule_type != RuleType.forbidden_phrase:
            return False, ""
        
        rule_phrases = set(rule.params.get("phrases", []))
        rule_stages = set(rule.applies_to_stages or [])
        
        for existing_rule in existing_rules:
            if existing_rule.id == rule.id:
                continue
            
            if existing_rule.rule_type != RuleType.required_phrase:
                continue
            
            # Check if they apply to the same stages
            existing_stages = set(existing_rule.applies_to_stages or [])
            
            # If both are call-wide or they share stages
            if (not rule_stages and not existing_stages) or (rule_stages & existing_stages):
                existing_phrases = set(existing_rule.params.get("phrases", []))
                
                # Check for exact phrase matches
                conflicting = rule_phrases & existing_phrases
                if conflicting:
                    return True, f"Forbidden phrase conflicts with required phrase: {conflicting}"
        
        return False, ""

