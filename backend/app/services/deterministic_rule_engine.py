"""
Phase 3: Deterministic Rule Engine
Evaluates FlowVersion steps and ComplianceRules deterministically per Phase 3 spec.
"""

from typing import Dict, List, Any, Optional, Tuple
from app.models.flow_version import FlowVersion
from app.models.flow_stage import FlowStage
from app.models.flow_step import FlowStep
from app.models.compliance_rule import ComplianceRule, RuleType, Severity
import re
import logging

logger = logging.getLogger(__name__)


class DeterministicRuleEngine:
    """
    Phase 3: Deterministic Rule Engine
    Evaluates steps and compliance rules deterministically.
    """
    
    def __init__(self):
        pass
    
    def normalize_text(self, text: str) -> str:
        """Normalize text for matching: lowercase, trim, collapse whitespace"""
        if not text:
            return ""
        # Lowercase, remove punctuation except apostrophes, collapse whitespace
        normalized = text.lower()
        normalized = re.sub(r"[^\w\s']", "", normalized)  # Remove punctuation except apostrophes
        normalized = re.sub(r"\s+", " ", normalized)  # Collapse whitespace
        return normalized.strip()
    
    def detect_step(
        self,
        step: FlowStep,
        segments: List[Dict[str, Any]]
    ) -> Tuple[bool, Optional[float], List[Dict[str, Any]]]:
        """
        Detect if a step occurred in transcript segments.
        Returns (detected, earliest_timestamp, evidence_snippets)
        """
        if not step.expected_phrases or len(step.expected_phrases) == 0:
            # Step has no expected phrases - cannot detect deterministically
            return False, None, []
        
        evidence = []
        earliest_timestamp = None
        
        # Search agent segments only
        for segment in segments:
            if segment.get("speaker") != "agent":
                continue
            
            segment_text = segment.get("text", "")
            normalized_segment = self.normalize_text(segment_text)
            
            # Check each expected phrase
            for phrase in step.expected_phrases:
                normalized_phrase = self.normalize_text(phrase)
                
                if normalized_phrase in normalized_segment:
                    timestamp = segment.get("start_time")
                    if timestamp is not None:
                        if earliest_timestamp is None or timestamp < earliest_timestamp:
                            earliest_timestamp = timestamp
                        
                        evidence.append({
                            "text": segment_text,
                            "start_time": timestamp,
                            "end_time": segment.get("end_time"),
                            "matched_phrase": phrase
                        })
        
        detected = len(evidence) > 0
        return detected, earliest_timestamp, evidence
    
    def evaluate_steps(
        self,
        flow_version: FlowVersion,
        segments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluate all steps in FlowVersion.
        Returns stage_results dict per Phase 3 spec.
        """
        stage_results = {}
        
        for stage in sorted(flow_version.stages, key=lambda s: s.order):
            step_results = []
            order_violations = []
            timing_violations = []
            
            # Detect each step
            step_timestamps = {}
            for step in sorted(stage.steps, key=lambda s: s.order):
                detected, timestamp, evidence = self.detect_step(step, segments)
                
                step_result = {
                    "step_id": step.id,
                    "passed": detected if not step.required else detected,  # Required steps must be detected
                    "detected": detected,
                    "timestamp": timestamp,
                    "evidence": evidence,
                    "reason_if_failed": None
                }
                
                if step.required and not detected:
                    step_result["reason_if_failed"] = "required_step_missing"
                    step_result["passed"] = False
                
                step_results.append(step_result)
                step_timestamps[step.id] = timestamp
            
            # Check step order within stage
            detected_steps = [(s["step_id"], s["timestamp"]) for s in step_results if s["detected"] and s["timestamp"] is not None]
            detected_steps.sort(key=lambda x: x[1])  # Sort by timestamp
            
            # Verify order matches step.order
            for i, (step_id, timestamp) in enumerate(detected_steps):
                step = next((s for s in stage.steps if s.id == step_id), None)
                if step:
                    # Check if any step with higher order appeared earlier
                    for j, (other_step_id, other_timestamp) in enumerate(detected_steps):
                        if j < i:  # Earlier in time
                            other_step = next((s for s in stage.steps if s.id == other_step_id), None)
                            if other_step and other_step.order > step.order:
                                order_violations.append(
                                    f"Step {step.name} (order {step.order}) appeared after step {other_step.name} (order {other_step.order})"
                                )
            
            # Check timing requirements
            call_start = 0.0
            for step_result in step_results:
                step = next((s for s in stage.steps if s.id == step_result["step_id"]), None)
                if step and step.timing_requirement:
                    timing_req = step.timing_requirement
                    if isinstance(timing_req, dict) and timing_req.get("enabled"):
                        seconds = timing_req.get("seconds", 0)
                        timestamp = step_result.get("timestamp")
                        
                        if timestamp is not None:
                            if timestamp - call_start > seconds:
                                timing_violations.append(
                                    f"{step.name} must occur within {seconds}s"
                                )
                        elif step.required:
                            # Required step with timing requirement but not detected
                            timing_violations.append(
                                f"{step.name} must occur within {seconds}s"
                            )
            
            stage_results[stage.id] = {
                "step_results": step_results,
                "order_violations": order_violations,
                "timing_violations": timing_violations
            }
        
        return stage_results
    
    def check_stage_order(
        self,
        flow_version: FlowVersion,
        stage_results: Dict[str, Any]
    ) -> List[str]:
        """Check that stages appear in correct order"""
        violations = []
        
        # Get earliest timestamp for each stage
        stage_timestamps = {}
        for stage_id, results in stage_results.items():
            step_results = results.get("step_results", [])
            timestamps = [s.get("timestamp") for s in step_results if s.get("timestamp") is not None]
            if timestamps:
                stage_timestamps[stage_id] = min(timestamps)
        
        # Check order
        stages_by_order = sorted(flow_version.stages, key=lambda s: s.order)
        for i, stage in enumerate(stages_by_order):
            if stage.id not in stage_timestamps:
                continue
            
            stage_time = stage_timestamps[stage.id]
            
            # Check if any later stage appeared earlier
            for later_stage in stages_by_order[i+1:]:
                if later_stage.id in stage_timestamps:
                    later_time = stage_timestamps[later_stage.id]
                    if later_time < stage_time:
                        violations.append(
                            f"Stage {later_stage.name} (order {later_stage.order}) appeared before stage {stage.name} (order {stage.order})"
                        )
        
        return violations
    
    def evaluate_compliance_rules(
        self,
        compliance_rules: List[ComplianceRule],
        flow_version: FlowVersion,
        segments: List[Dict[str, Any]],
        stage_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Evaluate compliance rules per Phase 2 spec.
        Returns list of RuleEvaluation dicts.
        """
        rule_evaluations = []
        
        # Get step timestamps from stage_results
        step_timestamps = {}
        for stage_id, results in stage_results.items():
            for step_result in results.get("step_results", []):
                if step_result.get("timestamp"):
                    step_timestamps[step_result["step_id"]] = step_result["timestamp"]
        
        # Get full transcript text
        transcript_text = " ".join([s.get("text", "") for s in segments])
        normalized_transcript = self.normalize_text(transcript_text)
        
        for rule in compliance_rules:
            if not rule.active:
                continue
            
            evaluation = {
                "rule_id": rule.id,
                "title": rule.title,
                "rule_type": rule.rule_type.value,
                "severity": rule.severity.value,
                "passed": True,
                "evidence": [],
                "violation_reason": None
            }
            
            params = rule.params
            applies_to_stages = rule.applies_to_stages or []
            
            # Determine scope segments
            scope_segments = segments
            if applies_to_stages:
                # Filter to segments within specified stages
                # For now, use all segments (stage boundaries would need to be detected)
                scope_segments = segments
            
            scope_text = " ".join([s.get("text", "") for s in scope_segments])
            normalized_scope = self.normalize_text(scope_text)
            
            if rule.rule_type == RuleType.required_phrase:
                phrases = params.get("phrases", [])
                match_type = params.get("match_type", "contains")
                found = False
                
                for phrase in phrases:
                    normalized_phrase = self.normalize_text(phrase)
                    
                    if match_type == "contains":
                        if normalized_phrase in normalized_scope:
                            found = True
                            # Find evidence
                            for segment in scope_segments:
                                if normalized_phrase in self.normalize_text(segment.get("text", "")):
                                    evaluation["evidence"].append({
                                        "type": "transcript_snippet",
                                        "text": segment.get("text", ""),
                                        "start_time": segment.get("start_time"),
                                        "end_time": segment.get("end_time"),
                                        "match_type": "contains"
                                    })
                                    break
                            break
                    elif match_type == "exact":
                        # Exact match logic
                        if normalized_phrase == normalized_scope or normalized_phrase in normalized_scope.split():
                            found = True
                            break
                    elif match_type == "regex":
                        if re.search(phrase, scope_text, re.IGNORECASE):
                            found = True
                            break
                
                if not found:
                    evaluation["passed"] = False
                    evaluation["violation_reason"] = "Required phrase not found"
            
            elif rule.rule_type == RuleType.forbidden_phrase:
                phrases = params.get("phrases", [])
                match_type = params.get("match_type", "contains")
                
                for phrase in phrases:
                    normalized_phrase = self.normalize_text(phrase)
                    
                    if match_type == "contains":
                        if normalized_phrase in normalized_scope:
                            evaluation["passed"] = False
                            evaluation["violation_reason"] = f"Forbidden phrase found: {phrase}"
                            # Find evidence
                            for segment in scope_segments:
                                if normalized_phrase in self.normalize_text(segment.get("text", "")):
                                    evaluation["evidence"].append({
                                        "type": "transcript_snippet",
                                        "text": segment.get("text", ""),
                                        "start_time": segment.get("start_time"),
                                        "end_time": segment.get("end_time"),
                                        "match_type": "contains"
                                    })
                                    break
                            break
                    elif match_type == "regex":
                        if re.search(phrase, scope_text, re.IGNORECASE):
                            evaluation["passed"] = False
                            evaluation["violation_reason"] = f"Forbidden phrase found: {phrase}"
                            break
            
            elif rule.rule_type == RuleType.sequence_rule:
                before_step_id = params.get("before_step_id")
                after_step_id = params.get("after_step_id")
                
                before_timestamp = step_timestamps.get(before_step_id)
                after_timestamp = step_timestamps.get(after_step_id)
                
                if before_timestamp is None or after_timestamp is None:
                    evaluation["passed"] = False
                    evaluation["violation_reason"] = "One or both steps not detected"
                elif after_timestamp < before_timestamp:
                    evaluation["passed"] = False
                    evaluation["violation_reason"] = f"Step {after_step_id} occurred before step {before_step_id}"
                    evaluation["evidence"] = [
                        {
                            "type": "timestamp",
                            "start_time": before_timestamp,
                            "end_time": None
                        },
                        {
                            "type": "timestamp",
                            "start_time": after_timestamp,
                            "end_time": None
                        }
                    ]
            
            elif rule.rule_type == RuleType.timing_rule:
                target = params.get("target")
                target_id_or_phrase = params.get("target_id_or_phrase")
                within_seconds = params.get("within_seconds", 0)
                reference = params.get("reference", "call_start")
                
                target_timestamp = None
                
                if target == "step":
                    target_timestamp = step_timestamps.get(target_id_or_phrase)
                elif target == "phrase":
                    # Find phrase timestamp
                    normalized_target = self.normalize_text(target_id_or_phrase)
                    for segment in scope_segments:
                        if normalized_target in self.normalize_text(segment.get("text", "")):
                            target_timestamp = segment.get("start_time")
                            break
                
                if target_timestamp is None:
                    evaluation["passed"] = False
                    evaluation["violation_reason"] = "Target not found"
                else:
                    reference_time = 0.0
                    if reference == "previous_step":
                        # Find previous step timestamp (simplified - would need step order)
                        reference_time = 0.0  # TODO: Implement previous step detection
                    
                    if target_timestamp - reference_time > within_seconds:
                        evaluation["passed"] = False
                        evaluation["violation_reason"] = f"Target occurred {target_timestamp - reference_time:.1f}s after reference (limit: {within_seconds}s)"
            
            elif rule.rule_type == RuleType.verification_rule:
                verification_step_id = params.get("verification_step_id")
                required_count = params.get("required_question_count", 0)
                must_complete_before = params.get("must_complete_before_step_id")
                
                # Count verification questions (simplified - would need pattern matching)
                verification_timestamp = step_timestamps.get(verification_step_id)
                before_timestamp = step_timestamps.get(must_complete_before)
                
                # Simplified: check if verification step occurred before resolution step
                if verification_timestamp is None:
                    evaluation["passed"] = False
                    evaluation["violation_reason"] = "Verification step not detected"
                elif before_timestamp and verification_timestamp > before_timestamp:
                    evaluation["passed"] = False
                    evaluation["violation_reason"] = "Verification occurred after resolution step"
                # TODO: Count actual KBA questions
            
            elif rule.rule_type == RuleType.conditional_rule:
                condition = params.get("condition", {})
                required_actions = params.get("required_actions", [])
                
                # Evaluate condition (simplified)
                condition_met = False
                # TODO: Implement condition evaluation (sentiment, phrase_mentioned, metadata_flag)
                
                if condition_met:
                    # Check required actions
                    actions_met = []
                    for action in required_actions:
                        action_type = action.get("action_type")
                        if action_type == "step_completed":
                            step_id = action.get("step_id")
                            if step_id in step_timestamps:
                                actions_met.append(True)
                        elif action_type == "phrase_spoken":
                            phrase = action.get("phrase", "")
                            if phrase.lower() in normalized_scope:
                                actions_met.append(True)
                    
                    if len(actions_met) == 0:
                        evaluation["passed"] = False
                        evaluation["violation_reason"] = "Required actions not met"
            
            rule_evaluations.append(evaluation)
        
        return rule_evaluations
    
    def calculate_deterministic_score(
        self,
        stage_results: Dict[str, Any],
        rule_evaluations: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate deterministic score per Phase 3 spec.
        step_score * 0.7 + rule_score * 0.3
        """
        # Calculate step score
        total_required_steps = 0
        completed_required_steps = 0
        
        for stage_id, results in stage_results.items():
            for step_result in results.get("step_results", []):
                # Check if step is required (would need step object, simplified)
                if step_result.get("reason_if_failed") == "required_step_missing":
                    total_required_steps += 1
                    if step_result.get("passed"):
                        completed_required_steps += 1
                elif step_result.get("detected"):
                    # Assume detected steps are required if they have expected_phrases
                    total_required_steps += 1
                    completed_required_steps += 1
        
        step_score = (completed_required_steps / total_required_steps * 100) if total_required_steps > 0 else 100
        
        # Calculate rule score
        total_rules = len(rule_evaluations)
        passed_rules = sum(1 for r in rule_evaluations if r.get("passed"))
        rule_score = (passed_rules / total_rules * 100) if total_rules > 0 else 100
        
        # Combined score
        deterministic_score = (step_score * 0.7) + (rule_score * 0.3)
        
        return round(deterministic_score, 2)
    
    def evaluate(
        self,
        flow_version: FlowVersion,
        compliance_rules: List[ComplianceRule],
        transcript_text: str,
        segments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Main evaluation method per Phase 3 spec.
        Returns DeterministicResult dict.
        """
        # Evaluate steps
        stage_results = self.evaluate_steps(flow_version, segments)
        
        # Check stage order
        stage_order_violations = self.check_stage_order(flow_version, stage_results)
        # Add to first stage's violations (or create summary)
        
        # Evaluate compliance rules
        rule_evaluations = self.evaluate_compliance_rules(
            compliance_rules,
            flow_version,
            segments,
            stage_results
        )
        
        # Calculate deterministic score
        deterministic_score = self.calculate_deterministic_score(stage_results, rule_evaluations)
        
        # Check for critical violations
        critical_failed = any(
            r.get("severity") == "critical" and not r.get("passed")
            for r in rule_evaluations
        )
        
        overall_passed = not critical_failed
        
        return {
            "stage_results": stage_results,
            "rule_evaluations": rule_evaluations,
            "deterministic_score": deterministic_score,
            "overall_passed": overall_passed
        }

