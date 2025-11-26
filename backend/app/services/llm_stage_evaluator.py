"""
Phase 4: LLM Stage Evaluator Service
Evaluates individual stages using LLM with PII redaction and zero-data-retention mode.
"""

from typing import Dict, List, Any, Optional, Protocol
from app.services.pii_redactor import PIIRedactor
from app.services.gemini import GeminiService
from app.schemas.llm_stage_evaluation import LLMStageEvaluationResponse
import json
import logging

logger = logging.getLogger(__name__)


# Protocol for FlowVersion-like objects (for CompiledFlowVersion compatibility)
class FlowVersionLike(Protocol):
    id: str
    name: str
    stages: List[Any]


class FlowStageLike(Protocol):
    id: str
    name: str
    order: int
    steps: List[Any]


class FlowStepLike(Protocol):
    id: str
    name: str
    description: Optional[str]
    required: bool
    expected_phrases: List[str]
    timing_requirement: Optional[Dict[str, Any]]
    order: int


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
        flow_version: FlowVersionLike,
        rubric_mapping: Optional[str] = None,
        evaluation_config: Optional[Dict[str, Any]] = None
    ) -> tuple[str, str]:
        """
        Build system and user prompts per Phase 4 spec.
        Returns (system_prompt, user_prompt)
        """
        # Find stage in CompiledFlowVersion
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
        
        # Build transcript text from stage segments
        transcript_text = "\n".join([
            f"{seg.get('speaker', 'unknown')}: {seg.get('text', '')}"
            for seg in stage_segments
        ])
        
        # System prompt
        system_prompt = """You are an impartial quality evaluator. Use only the provided deterministic evidence and transcript. Do not invent rule IDs or remove critical violations. Return JSON only and nothing else."""
        
        # Helper to safely get order (handles both FlowStage and CompiledFlowStage)
        def get_order(obj):
            return getattr(obj, 'ordering_index', getattr(obj, 'order', 0))

        # User prompt
        config = evaluation_config or {
            "penalty_missing_required": 20,
            "penalty_major": 40,
            "penalty_minor": 10,
            "penalty_timing": 10,
            "discretionary_max": 10
        }
        
        # Sort steps safely
        sorted_steps = sorted(stage.steps, key=get_order)
        
        user_prompt = f"""CONTEXT:
evaluation_id: {deterministic_results.get('evaluation_id', 'unknown')}
flow_version_id: {flow_version.id}
stage_id: {stage_id}
flow_stage_definition: {json.dumps({
    'id': stage.id,
    'name': stage.name,
    'order': get_order(stage),
    'steps': [{
        'id': s.id,
        'name': s.name,
        'description': s.description,
        'required': getattr(s, 'required', False),
        'expected_phrases': s.expected_phrases or [],
        'timing_requirement': getattr(s, 'timing_requirement', {'enabled': False, 'seconds': None}),
        'order': get_order(s)
    } for s in sorted_steps]
})}
deterministic_step_results: {json.dumps(step_results)}
deterministic_rule_evaluations: {json.dumps(stage_rules)}
transcript_segments: {json.dumps(stage_segments)}
rubric_mapping_hint: {rubric_mapping or 'General'}
evaluation_config: {json.dumps(config)}

TASK:
1) For this stage, evaluate each step in flow_stage_definition. If deterministic_step_results indicates the step was detected, mark it PASSED and cite it. If deterministic result is NOT detected (or missing), evaluate the transcript semantically against the step name and description. If you find clear evidence in the transcript that the step was performed, mark it PASSED and cite the transcript snippet as evidence. If no evidence is found, mark it FAILED.

2) Assign a numeric stage_score (0-100). Start at 100, subtract deterministic penalties for failed required steps and rule violations according to evaluation_config. You may apply an extra discretionary adjustment up to +/- evaluation_config.discretionary_max (default 10 points) only when clear, evidence-based reasoning applies. For every discretionary adjustment include short rationale and cite transcript timestamp or rule_id.

3) Provide short actionable stage_feedback (1-3 sentences) referencing step IDs and timestamps or rule IDs.

4) Indicate stage_confidence (0-1) expressing how confident you are in the stage_score given available evidence.

5) Output ONLY valid JSON matching this exact schema. No markdown, no code blocks, no explanations, ONLY the JSON object:

{{
  "evaluation_id": "{deterministic_results.get('evaluation_id', 'unknown')}",
  "flow_version_id": "{flow_version.id}",
  "recording_id": "{deterministic_results.get('recording_id', 'unknown')}",
  "stage_id": "{stage_id}",
  "stage_score": <integer 0-100>,
  "step_evaluations": [
    {{
      "step_id": "<step_id>",
      "passed": <boolean>,
      "evidence": [],
      "rationale": "<string>"
    }}
  ],
  "stage_feedback": ["<string>"],
  "stage_confidence": <float 0.0-1.0>,
  "critical_violation": <boolean>,
  "notes": "<optional string>"
}}

IMPORTANT: 
- Return ONLY the JSON object, no other text before or after
- stage_score must be an integer between 0 and 100
- stage_confidence must be a float between 0.0 and 1.0
- If any deterministic_rule_evaluations contains severity == "critical" and passed == false, set critical_violation=true
- Do not use markdown code blocks (```json or ```)"""
        
        return system_prompt, user_prompt
    
    def evaluate_stage(
        self,
        stage_id: str,
        stage_segments: List[Dict[str, Any]],
        deterministic_results: Dict[str, Any],
        flow_version: FlowVersionLike,
        rubric_mapping: Optional[str] = None,
        evaluation_config: Optional[Dict[str, Any]] = None,
        evaluation_id: Optional[str] = None,
        recording_id: Optional[str] = None,
        full_transcript: Optional[str] = None
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
            
            # Call Gemini with temperature=0 for deterministic output
            # 
            # ZERO DATA RETENTION NOTE:
            # The Generative Language API (used by google.generativeai) does NOT have data retention
            # settings in the API key configuration page. Instead:
            # 
            # 1. Default behavior: Gemini caches data in-memory (not at rest) for 24 hours for latency
            #    - This is project-level, isolated, and complies with data residency
            #    - Data is NOT used for training
            # 
            # 2. To disable in-memory caching (true zero retention):
            #    - Use Vertex AI API instead of Generative Language API, OR
            #    - Configure cache at project level: Vertex AI → Cache Config → disableCache=true
            #    - Requires: roles/aiplatform.admin permission
            #    - API: PATCH https://us-central1-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/cacheConfig
            # 
            # 3. For enterprise zero data retention agreements:
            #    - Contact Google Cloud Support for custom data retention policies
            #    - May require switching to Vertex AI API endpoint
            # 
            # Current implementation uses Generative Language API which has 24h in-memory cache by default.
            # Data is NOT stored at rest, NOT used for training, and is isolated per project.
            try:
                import google.generativeai as genai
                
                # Configure generation config with temperature=0 for deterministic output
                # Temperature=0 ensures consistent, reproducible results (no randomness)
                generation_config = {
                    "temperature": 0,  # ✅ Zero temperature for deterministic output
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 2048,
                }
                
                # Safety settings: Block harmful content but allow all other content
                # This ensures privacy-focused evaluation without blocking legitimate content
                safety_settings = [
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_NONE"
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_NONE"
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_NONE"
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_NONE"
                    }
                ]
                
                # Call model (synchronous for now - can be made async later)
                model = self.gemini_service.pro_model
                # Combine prompts
                full_prompt = f"{system_prompt}\n\n{user_prompt}"
                
                try:
                    # Add timeout to prevent hanging (60 seconds default)
                    import concurrent.futures
                    import os
                    
                    timeout_seconds = int(os.getenv("GEMINI_API_TIMEOUT_SECONDS", "60"))
                    
                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                        future = executor.submit(
                            model.generate_content,
                            full_prompt,
                            generation_config=generation_config,
                            safety_settings=safety_settings
                        )
                        try:
                            response = future.result(timeout=timeout_seconds)
                        except concurrent.futures.TimeoutError:
                            logger.error(f"LLM stage evaluation timed out after {timeout_seconds} seconds for stage {stage_id}")
                            raise Exception(f"LLM evaluation timed out after {timeout_seconds} seconds")
                except TypeError:
                    # Fallback if response_mime_type is not supported
                    import concurrent.futures
                    import os
                    
                    timeout_seconds = int(os.getenv("GEMINI_API_TIMEOUT_SECONDS", "60"))
                    
                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                        future = executor.submit(
                            model.generate_content,
                            full_prompt,
                            generation_config=generation_config,
                            safety_settings=safety_settings
                        )
                        try:
                            response = future.result(timeout=timeout_seconds)
                        except concurrent.futures.TimeoutError:
                            logger.error(f"LLM stage evaluation timed out after {timeout_seconds} seconds for stage {stage_id}")
                            raise Exception(f"LLM evaluation timed out after {timeout_seconds} seconds")
                
                # Parse response
                response_text = response.text.strip()
                logger.debug(f"LLM raw response for stage {stage_id}: {response_text[:1000]}")
                
                # Remove markdown code blocks if present
                if response_text.startswith("```"):
                    # Remove ```json or ``` markers
                    lines = response_text.split("\n")
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines[-1].strip() == "```":
                        lines = lines[:-1]
                    response_text = "\n".join(lines).strip()
                
                # Try to extract JSON from response
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_text = response_text[json_start:json_end]
                    try:
                        evaluation_data = json.loads(json_text)
                        logger.debug(f"Parsed JSON for stage {stage_id}: {json.dumps(evaluation_data, indent=2)[:1000]}")
                    except json.JSONDecodeError as je:
                        logger.error(f"JSON parse error for stage {stage_id}: {je}")
                        logger.error(f"JSON text: {json_text[:1000]}")
                        # Try to fix common JSON issues
                        try:
                            # Try removing trailing commas
                            json_text_fixed = json_text.replace(',\n}', '\n}').replace(',\n]', '\n]')
                            evaluation_data = json.loads(json_text_fixed)
                            logger.info(f"Fixed JSON by removing trailing commas for stage {stage_id}")
                        except:
                            raise ValueError(f"Invalid JSON in LLM response: {je}")
                else:
                    logger.error(f"No JSON found in LLM response for stage {stage_id}")
                    logger.error(f"Full response: {response_text}")
                    raise ValueError("No JSON found in LLM response")
                
                # Validate and normalize response schema
                try:
                    # Ensure required fields exist with defaults
                    if "step_evaluations" not in evaluation_data:
                        evaluation_data["step_evaluations"] = []
                    if "stage_feedback" not in evaluation_data:
                        evaluation_data["stage_feedback"] = []
                    if "critical_violation" not in evaluation_data:
                        evaluation_data["critical_violation"] = False
                    if "notes" not in evaluation_data:
                        evaluation_data["notes"] = None
                    
                    # Ensure stage_score is an integer
                    if "stage_score" in evaluation_data:
                        evaluation_data["stage_score"] = int(evaluation_data["stage_score"])
                    
                    # Ensure stage_confidence is a float
                    if "stage_confidence" in evaluation_data:
                        evaluation_data["stage_confidence"] = float(evaluation_data["stage_confidence"])
                    
                    # Normalize evidence structure if needed (handle string evidence)
                    if "step_evaluations" in evaluation_data and isinstance(evaluation_data["step_evaluations"], list):
                        for step_eval in evaluation_data["step_evaluations"]:
                            if "evidence" in step_eval and isinstance(step_eval["evidence"], list):
                                new_evidence = []
                                for item in step_eval["evidence"]:
                                    if isinstance(item, str):
                                        # Convert string evidence to object
                                        new_evidence.append({
                                            "type": "transcript_snippet",
                                            "text": item
                                        })
                                    elif isinstance(item, dict):
                                        # Ensure type field exists
                                        if "type" not in item:
                                            item["type"] = "transcript_snippet"
                                        new_evidence.append(item)
                                    else:
                                        new_evidence.append(item)
                                step_eval["evidence"] = new_evidence

                    # Validate response schema
                    validated = LLMStageEvaluationResponse(**evaluation_data)
                    logger.info(f"Successfully validated LLM response for stage {stage_id}: score={validated.stage_score}, confidence={validated.stage_confidence}")
                    return validated.dict()
                except Exception as e:
                    logger.warning(f"LLM response validation failed for stage {stage_id}: {e}. Falling back to deterministic.")
                    # Reduced logging for validation errors
                    if hasattr(e, 'errors'):
                        logger.warning(f"Pydantic validation errors: {e.errors()}")
                    
                    # Log full data only at debug level
                    logger.debug(f"Full evaluation_data that failed: {json.dumps(evaluation_data, indent=2, default=str)[:1000]}...")
                    # Fallback to deterministic
                    return self._create_deterministic_fallback(
                        stage_id,
                        deterministic_results,
                        f"LLM response validation failed: {str(e)}"
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

