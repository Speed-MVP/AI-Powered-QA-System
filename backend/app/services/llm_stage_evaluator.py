"""
Phase 4: LLM Stage Evaluator Service
Evaluates individual stages using LLM with PII redaction and zero-data-retention mode.
"""

from typing import Dict, List, Any, Optional
from app.models.flow_version import FlowVersion
from app.models.flow_stage import FlowStage
from app.services.pii_redactor import PIIRedactor
from app.services.gemini import GeminiService
from app.schemas.llm_stage_evaluation import LLMStageEvaluationResponse
import json
import logging

logger = logging.getLogger(__name__)


class LLMStageEvaluator:
    """
    Phase 4: LLM Stage Evaluator
    Evaluates stages using LLM with PII redaction and structured output.
    """
    
    def __init__(self):
        self.pii_redactor = PIIRedactor()
        self.gemini_service = GeminiService()
    
    def build_prompt(
        self,
        stage_id: str,
        stage_segments: List[Dict[str, Any]],
        deterministic_results: Dict[str, Any],
        flow_version: FlowVersion,
        rubric_mapping: Optional[str] = None,
        evaluation_config: Optional[Dict[str, Any]] = None
    ) -> tuple[str, str]:
        """
        Build system and user prompts per Phase 4 spec.
        Returns (system_prompt, user_prompt)
        """
        # Find stage in FlowVersion
        stage = next((s for s in flow_version.stages if s.id == stage_id), None)
        if not stage:
            raise ValueError(f"Stage {stage_id} not found in FlowVersion")
        
        # Get deterministic step results for this stage
        stage_deterministic = deterministic_results.get("stage_results", {}).get(stage_id, {})
        step_results = stage_deterministic.get("step_results", [])
        
        # Get rule evaluations relevant to this stage
        rule_evaluations = deterministic_results.get("rule_evaluations", [])
        stage_rules = [
            r for r in rule_evaluations
            if not r.get("applies_to_stages") or stage_id in r.get("applies_to_stages", [])
        ]
        
        # Build transcript segments text
        transcript_text = "\n".join([
            f"{seg.get('speaker', 'unknown')}: {seg.get('text', '')}"
            for seg in stage_segments
        ])
        
        # System prompt
        system_prompt = """You are an impartial quality evaluator. Use only the provided deterministic evidence and transcript. Do not invent rule IDs or remove critical violations. Return JSON only and nothing else."""
        
        # User prompt
        config = evaluation_config or {
            "penalty_missing_required": 20,
            "penalty_major": 40,
            "penalty_minor": 10,
            "penalty_timing": 10,
            "discretionary_max": 10
        }
        
        user_prompt = f"""CONTEXT:
evaluation_id: {deterministic_results.get('evaluation_id', 'unknown')}
flow_version_id: {flow_version.id}
stage_id: {stage_id}
flow_stage_definition: {json.dumps({
    'id': stage.id,
    'name': stage.name,
    'order': stage.order,
    'steps': [{
        'id': s.id,
        'name': s.name,
        'description': s.description,
        'required': s.required,
        'expected_phrases': s.expected_phrases or [],
        'timing_requirement': s.timing_requirement or {'enabled': False, 'seconds': None},
        'order': s.order
    } for s in sorted(stage.steps, key=lambda x: x.order)]
})}
deterministic_step_results: {json.dumps(step_results)}
deterministic_rule_evaluations: {json.dumps(stage_rules)}
transcript_segments: {json.dumps(stage_segments)}
rubric_mapping_hint: {rubric_mapping or 'General'}
evaluation_config: {json.dumps(config)}

TASK:
1) For this stage, evaluate each step in flow_stage_definition. Use deterministic_step_results to decide PASS/FAIL; if deterministic result exists, cite it. If no deterministic evidence exists for a step that is required, mark it failed and cite 'no evidence'. Do not invent evidence.

2) Assign a numeric stage_score (0-100). Start at 100, subtract deterministic penalties for failed required steps and rule violations according to evaluation_config. You may apply an extra discretionary adjustment up to +/- evaluation_config.discretionary_max (default 10 points) only when clear, evidence-based reasoning applies. For every discretionary adjustment include short rationale and cite transcript timestamp or rule_id.

3) Provide short actionable stage_feedback (1-3 sentences) referencing step IDs and timestamps or rule IDs.

4) Indicate stage_confidence (0-1) expressing how confident you are in the stage_score given available evidence.

5) Output JSON exactly matching the schema. No other text.

IMPORTANT: If any deterministic_rule_evaluations contains severity == "critical" and passed == false, include field `critical_violation=true` and do not set overall pass flag here (overall decision handled downstream). You must not override or nullify a critical failure."""
        
        return system_prompt, user_prompt
    
    def evaluate_stage(
        self,
        stage_id: str,
        stage_segments: List[Dict[str, Any]],
        deterministic_results: Dict[str, Any],
        flow_version: FlowVersion,
        rubric_mapping: Optional[str] = None,
        evaluation_config: Optional[Dict[str, Any]] = None,
        evaluation_id: Optional[str] = None,
        recording_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a single stage using LLM.
        Returns LLMStageEvaluationResponse dict or fallback dict.
        """
        try:
            # Redact PII from segments
            redacted_segments = self.pii_redactor.redact_segments(stage_segments)
            
            # Build prompts
            system_prompt, user_prompt = self.build_prompt(
                stage_id,
                redacted_segments,
                deterministic_results,
                flow_version,
                rubric_mapping,
                evaluation_config
            )
            
            # Call Gemini with zero-data-retention mode
            # Note: Gemini API may not support zero-data-retention flag directly
            # This should be configured at the API level or via model configuration
            try:
                import google.generativeai as genai
                
                # Configure generation config with temperature=0 for deterministic output
                generation_config = {
                    "temperature": 0,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 2048,
                }
                
                # Call model (synchronous for now - can be made async later)
                model = self.gemini_service.pro_model
                # Combine prompts
                full_prompt = f"{system_prompt}\n\n{user_prompt}"
                response = model.generate_content(
                    full_prompt,
                    generation_config=generation_config
                )
                
                # Parse response
                response_text = response.text.strip()
                
                # Try to extract JSON from response
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_text = response_text[json_start:json_end]
                    evaluation_data = json.loads(json_text)
                else:
                    raise ValueError("No JSON found in LLM response")
                
                # Validate response schema
                try:
                    validated = LLMStageEvaluationResponse(**evaluation_data)
                    return validated.dict()
                except Exception as e:
                    logger.error(f"LLM response validation failed: {e}")
                    logger.error(f"Response: {response_text[:500]}")
                    # Fallback to deterministic
                    return self._create_deterministic_fallback(
                        stage_id,
                        deterministic_results,
                        "LLM response validation failed"
                    )
            
            except Exception as e:
                logger.error(f"LLM API call failed: {e}", exc_info=True)
                return self._create_deterministic_fallback(
                    stage_id,
                    deterministic_results,
                    f"LLM API error: {str(e)}"
                )
        
        except Exception as e:
            logger.error(f"Stage evaluation failed: {e}", exc_info=True)
            return self._create_deterministic_fallback(
                stage_id,
                deterministic_results,
                f"Evaluation error: {str(e)}"
            )
    
    def _create_deterministic_fallback(
        self,
        stage_id: str,
        deterministic_results: Dict[str, Any],
        reason: str
    ) -> Dict[str, Any]:
        """Create fallback evaluation using deterministic results"""
        stage_deterministic = deterministic_results.get("stage_results", {}).get(stage_id, {})
        step_results = stage_deterministic.get("step_results", [])
        
        # Calculate basic score from deterministic results
        total_steps = len(step_results)
        passed_steps = sum(1 for s in step_results if s.get("passed"))
        base_score = (passed_steps / total_steps * 100) if total_steps > 0 else 0
        
        # Check for critical violations
        rule_evaluations = deterministic_results.get("rule_evaluations", [])
        critical_violation = any(
            r.get("severity") == "critical" and not r.get("passed")
            for r in rule_evaluations
        )
        
        return {
            "evaluation_id": deterministic_results.get("evaluation_id", "unknown"),
            "flow_version_id": deterministic_results.get("flow_version_id", "unknown"),
            "recording_id": deterministic_results.get("recording_id", "unknown"),
            "stage_id": stage_id,
            "stage_score": int(base_score),
            "step_evaluations": [
                {
                    "step_id": s.get("step_id"),
                    "passed": s.get("passed", False),
                    "evidence": s.get("evidence", []),
                    "rationale": s.get("reason_if_failed") or "Deterministic evaluation"
                }
                for s in step_results
            ],
            "stage_feedback": [f"LLM evaluation failed - using deterministic fallback: {reason}"],
            "stage_confidence": 0.5,
            "critical_violation": critical_violation,
            "notes": f"LLM failed — using deterministic fallback: {reason}"
        }

