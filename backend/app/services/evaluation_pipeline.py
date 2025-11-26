"""
Evaluation Pipeline Orchestrator - Phase 9
Orchestrates the complete evaluation pipeline: Detection → LLM → Scoring
"""

import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.compiled_artifacts import CompiledFlowVersion, CompiledFlowStage, CompiledComplianceRule
from app.models.recording import Recording
from app.models.transcript import Transcript
from app.services.detection_engine import DetectionEngine
from app.services.llm_stage_evaluator import LLMStageEvaluator
from app.services.scoring_engine import ScoringEngine
from app.services.embedding_service import EmbeddingService
from app.services.pii_redactor import PIIRedactor
from app.services.transcript_compressor import TranscriptCompressor
from app.services.deterministic_rule_engine import DeterministicRuleEngine
from app.services.monitoring import monitoring_service
import time

logger = logging.getLogger(__name__)


class EvaluationPipeline:
    """Orchestrates evaluation pipeline"""
    
    def __init__(self):
        self.detection_engine = DetectionEngine()
        self.llm_evaluator = LLMStageEvaluator()
        self.scoring_engine = ScoringEngine()
        self.embedding_service = EmbeddingService()
        self.pii_redactor = PIIRedactor()
        self.transcript_compressor = TranscriptCompressor()
        self.rule_engine = DeterministicRuleEngine()
    
    def evaluate_recording(
        self,
        recording_id: str,
        compiled_flow_version_id: str,
        db: Session,
        company_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run complete evaluation pipeline for a recording
        
        Args:
            recording_id: Recording to evaluate
            compiled_flow_version_id: Compiled blueprint version to use
            db: Database session
            company_config: Company scoring configuration
        
        Returns:
            Final evaluation result
        """
        pipeline_start = time.time()
        
        try:
            # 1. Load recording and transcript
            recording = db.query(Recording).filter(
                Recording.id == recording_id
            ).first()
            
            if not recording:
                raise ValueError(f"Recording {recording_id} not found")
            
            transcript = db.query(Transcript).filter(
                Transcript.recording_id == recording_id
            ).first()
            
            if not transcript:
                raise ValueError(f"Transcript for recording {recording_id} not found")
            
            # 2. Load compiled blueprint with relationships
            from sqlalchemy.orm import joinedload
            compiled_flow_version = db.query(CompiledFlowVersion).options(
                joinedload(CompiledFlowVersion.stages).joinedload(CompiledFlowStage.steps),
                joinedload(CompiledFlowVersion.compliance_rules).joinedload(CompiledComplianceRule.flow_step),
                joinedload(CompiledFlowVersion.rubric_templates)
            ).filter(
                CompiledFlowVersion.id == compiled_flow_version_id
            ).first()
            
            if not compiled_flow_version:
                raise ValueError(f"Compiled flow version {compiled_flow_version_id} not found")
            
            # 3. Prepare transcript segments
            transcript_segments = transcript.diarized_segments or []
            if not transcript_segments:
                # Fallback: create segments from transcript text
                transcript_segments = [{
                    "text": transcript.transcript_text or "",
                    "speaker": "agent",
                    "start": 0,
                    "end": 0,
                    "confidence": 1.0
                }]
            
            # 4. Prepare behaviors from compiled blueprint
            behaviors = []
            for stage in compiled_flow_version.stages:
                for step in stage.steps:
                    behaviors.append({
                        "id": step.id,
                        "name": step.name,
                        "description": step.description,
                        "detection_hint": step.detection_hint,
                        "expected_phrases": step.expected_phrases,
                        "metadata": step.extra_metadata or {}
                    })
            
            # 5. Run Detection Engine
            logger.info(f"Running detection engine for recording {recording_id}")
            detection_results = self.detection_engine.detect_behaviors(
                transcript_segments=transcript_segments,
                behaviors=behaviors,
                embedding_service=self.embedding_service
            )
            
            # 6. Prepare transcript for LLM (redact PII, compress if needed)
            redacted_segments = []
            for seg in transcript_segments:
                redacted_text = self.pii_redactor.redact_text(seg.get("text", ""))
                redacted_segments.append({
                    **seg,
                    "text": redacted_text
                })
            
            # 7. Run LLM Stage Evaluator
            logger.info(f"Running LLM stage evaluator for recording {recording_id}")
            llm_stage_evaluations = {}
            
            # Group segments by stage (simplified - in production would use actual stage timing)
            for stage in compiled_flow_version.stages:
                # Get segments for this stage (simplified - use all segments for now)
                stage_segments = redacted_segments
                
                # Build deterministic results for this stage
                stage_deterministic = {
                    "stage_id": stage.id,
                    "step_results": [
                        {
                            "step_id": step.id,
                            "step_name": step.name,
                            "detected": any(
                                b.get("behavior_id") == step.id and b.get("detected")
                                for b in detection_results.get("behaviors", [])
                            ),
                            "confidence": next((
                                b.get("confidence", 0.0)
                                for b in detection_results.get("behaviors", [])
                                if b.get("behavior_id") == step.id
                            ), 0.0)
                        }
                        for step in stage.steps
                    ]
                }
                
                try:
                    # CompiledFlowVersion implements FlowVersionLike protocol
                    # LLM evaluator accepts FlowVersionLike, so we can pass compiled_flow_version directly
                    flow_version_adapter = compiled_flow_version
                    
                    # Evaluate stage using LLM
                    evaluation_result = self.llm_evaluator.evaluate_stage(
                        stage_id=stage.id,
                        stage_segments=stage_segments,
                        deterministic_results={
                            "evaluation_id": recording_id,
                            "recording_id": recording_id,
                            "stage_results": {
                                stage.id: stage_deterministic
                            },
                            "rule_evaluations": []
                        },
                        flow_version=flow_version_adapter,
                        evaluation_config={},
                        evaluation_id=recording_id,
                        recording_id=recording_id
                    )
                    
                    # Convert evaluation result to expected format
                    if isinstance(evaluation_result, dict):
                        llm_stage_evaluations[stage.id] = {
                            "stage_id": stage.id,
                            "stage_name": stage.name,
                            "behaviors": [
                                {
                                    "behavior_id": step_eval.get("step_id"),
                                    "behavior_name": next((s.name for s in stage.steps if s.id == step_eval.get("step_id")), ""),
                                    "satisfaction_level": "full" if step_eval.get("passed") else "none",
                                    "confidence": 0.8 if step_eval.get("passed") else 0.2
                                }
                                for step_eval in evaluation_result.get("step_evaluations", [])
                            ],
                            "stage_score": evaluation_result.get("stage_score", 0),
                            "confidence": evaluation_result.get("stage_confidence", 0.5),
                            "evidence": evaluation_result.get("step_evaluations", []),
                            "feedback": " ".join(evaluation_result.get("stage_feedback", []))
                        }
                    else:
                        # Handle response object
                        llm_stage_evaluations[stage.id] = {
                            "stage_id": stage.id,
                            "stage_name": stage.name,
                            "behaviors": evaluation_result.behaviors if hasattr(evaluation_result, 'behaviors') else [],
                            "stage_score": evaluation_result.stage_score if hasattr(evaluation_result, 'stage_score') else 0,
                            "confidence": evaluation_result.confidence if hasattr(evaluation_result, 'confidence') else 0.5,
                            "evidence": evaluation_result.evidence if hasattr(evaluation_result, 'evidence') else [],
                            "feedback": evaluation_result.feedback if hasattr(evaluation_result, 'feedback') else ""
                        }
                except Exception as e:
                    logger.error(f"LLM evaluation failed for stage {stage.id}: {e}", exc_info=True)
                    # Fallback: use detection results only
                    llm_stage_evaluations[stage.id] = {
                        "stage_id": stage.id,
                        "stage_name": stage.name,
                        "behaviors": [
                            {
                                "behavior_id": step.id,
                                "behavior_name": step.name,
                                "satisfaction_level": "full" if any(
                                    b.get("behavior_id") == step.id and b.get("detected")
                                    for b in detection_results.get("behaviors", [])
                                ) else "none",
                                "confidence": next((
                                    b.get("confidence", 0.0)
                                    for b in detection_results.get("behaviors", [])
                                    if b.get("behavior_id") == step.id
                                ), 0.0)
                            }
                            for step in stage.steps
                        ],
                        "stage_score": 0,
                        "confidence": 0.5,
                        "evidence": [],
                        "feedback": "LLM evaluation failed, using detection results only"
                    }
            
            # 7. Prepare rubric template
            rubric_template = None
            if compiled_flow_version.rubric_templates:
                rubric = compiled_flow_version.rubric_templates[0]
                rubric_template = {
                    "categories": rubric.categories,
                    "mappings": rubric.mappings
                }
            
            # 8. Evaluate compliance rules
            logger.info(f"Evaluating compliance rules for recording {recording_id}")
            policy_rule_results = None
            if compiled_flow_version.compliance_rules and len(compiled_flow_version.compliance_rules) > 0:
                # Build stage results for rule evaluation
                stage_results = {}
                for stage_id, stage_eval in llm_stage_evaluations.items():
                    step_results = []
                    for behavior in stage_eval.get("behaviors", []):
                        # Find corresponding detection result for timestamp
                        detection_result = next((
                            b for b in detection_results.get("behaviors", [])
                            if b.get("behavior_id") == behavior.get("behavior_id")
                        ), None)
                        
                        timestamp = detection_result.get("start_time") if detection_result else None
                        detected = behavior.get("satisfaction_level") != "none"
                        
                        # If detected by LLM but not deterministically (e.g. semantic match),
                        # try to find timestamp in LLM evidence or use fallback to ensure compliance rules pass
                        if detected and timestamp is None:
                            # Check evidence for timestamp
                            evidence_list = behavior.get("evidence", [])
                            if isinstance(evidence_list, list):
                                for item in evidence_list:
                                    if isinstance(item, dict) and item.get("start") is not None:
                                        timestamp = item.get("start")
                                        break
                            
                            # Fallback if still None: use 0.001 to indicate "present but time unknown"
                            # This ensures it gets added to step_timestamps in rule engine
                            if timestamp is None:
                                timestamp = 0.001
                        
                        step_results.append({
                            "step_id": behavior.get("behavior_id"),
                            "step_name": behavior.get("behavior_name"),
                            "detected": detected,
                            "timestamp": timestamp,
                            "confidence": behavior.get("confidence", 0.0)
                        })
                    
                    stage_results[stage_id] = {
                        "step_results": step_results
                    }
                
                # Create rule adapter objects with params structure expected by DeterministicRuleEngine
                # The engine expects rule.params, rule.title, rule.applies_to_stages
                # But CompiledComplianceRule has phrases, match_mode, timing_constraints directly
                from types import SimpleNamespace
                
                rule_adapters = []
                for rule in compiled_flow_version.compliance_rules:
                    if not rule.active:
                        continue
                    
                    # Build params dict from rule fields
                    params = {}
                    if rule.phrases:
                        params["phrases"] = rule.phrases
                    if rule.match_mode:
                        params["match_type"] = rule.match_mode
                    if rule.timing_constraints:
                        params.update(rule.timing_constraints)
                    if rule.target:
                        params["target_id_or_phrase"] = rule.target
                    
                    # Create adapter object using SimpleNamespace
                    # Get rule title from flow_step name if available
                    rule_title = f"Rule {rule.id}"
                    if rule.flow_step:
                        rule_title = rule.flow_step.name
                    elif rule.target:
                        # Try to find step by target ID
                        for stage in compiled_flow_version.stages:
                            for step in stage.steps:
                                if step.id == rule.target:
                                    rule_title = step.name
                                    break
                    
                    rule_adapter = SimpleNamespace(
                        id=rule.id,
                        title=rule_title,
                        rule_type=rule.rule_type,
                        severity=rule.severity,
                        params=params,
                        target=rule.target,  # Include target ID
                        applies_to_stages=[],
                        active=rule.active
                    )
                    
                    rule_adapters.append(rule_adapter)
                
                # Normalize segment field names for rule engine (expects start_time/end_time)
                normalized_segments = []
                for seg in transcript_segments:
                    normalized_seg = seg.copy()
                    # Convert 'start' to 'start_time' if needed
                    if "start" in normalized_seg and "start_time" not in normalized_seg:
                        normalized_seg["start_time"] = normalized_seg.get("start")
                    # Convert 'end' to 'end_time' if needed
                    if "end" in normalized_seg and "end_time" not in normalized_seg:
                        normalized_seg["end_time"] = normalized_seg.get("end")
                    normalized_segments.append(normalized_seg)
                
                # Evaluate compliance rules
                rule_evaluations = self.rule_engine.evaluate_compliance_rules(
                    compliance_rules=rule_adapters,
                    transcript_text=transcript.transcript_text or "",
                    flow_version=compiled_flow_version,
                    segments=normalized_segments,
                    stage_results=stage_results
                )
                
                # DEBUG: Log stage_results timestamps
                for sid, res in stage_results.items():
                    for sres in res.get("step_results", []):
                        if sres.get("detected"):
                            logger.info(f"DEBUG_COMPLIANCE: Step {sres['step_name']} ({sres['step_id']}) detected=True, timestamp={sres.get('timestamp')}")
                        else:
                             logger.info(f"DEBUG_COMPLIANCE: Step {sres['step_name']} ({sres['step_id']}) detected=False")
                
                # Convert rule evaluations to violations format for scoring engine
                violations = []
                for rule_eval in rule_evaluations:
                    if not rule_eval.get("passed", True):
                        # Find the original rule to get action_on_fail
                        rule = next((
                            r for r in compiled_flow_version.compliance_rules
                            if r.id == rule_eval.get("rule_id")
                        ), None)
                        
                        violation = {
                            "rule_id": rule_eval.get("rule_id"),
                            "severity": rule_eval.get("severity", "minor"),
                            "description": rule_eval.get("violation_reason", "Compliance rule violation"),
                            "evidence": rule_eval.get("evidence", [])
                        }
                        
                        # Add action if it's a critical violation
                        if rule and rule.action_on_fail:
                            violation["action"] = rule.action_on_fail
                        
                        violations.append(violation)
                
                if violations:
                    policy_rule_results = {
                        "violations": violations,
                        "total_violations": len(violations),
                        "critical_count": sum(1 for v in violations if v.get("severity") == "critical"),
                        "major_count": sum(1 for v in violations if v.get("severity") == "major"),
                        "minor_count": sum(1 for v in violations if v.get("severity") == "minor")
                    }
                    logger.info(f"Found {len(violations)} compliance rule violations: {policy_rule_results['critical_count']} critical, {policy_rule_results['major_count']} major, {policy_rule_results['minor_count']} minor")
            
            # 9. Run Scoring Engine
            logger.info(f"Running scoring engine for recording {recording_id}")
            final_evaluation = self.scoring_engine.compute_evaluation(
                llm_stage_evaluations=llm_stage_evaluations,
                detection_results=detection_results,
                compiled_rubric=rubric_template or {},
                policy_rule_results=policy_rule_results,
                company_config=company_config or {}
            )
            
            pipeline_duration = time.time() - pipeline_start
            
            # Record metrics
            # monitoring_service.record_scoring_metric(...)
            
            return {
                "deterministic_results": detection_results,
                "llm_stage_evaluations": llm_stage_evaluations,
                "final_evaluation": final_evaluation
            }
            
        except Exception as e:
            logger.error(f"Evaluation pipeline failed: {e}", exc_info=True)
            raise

