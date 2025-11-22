"""
Phase 4: LLM Stage Evaluation Schemas
Pydantic schemas for LLM stage evaluation responses.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from datetime import datetime


class EvidenceItem(BaseModel):
    type: str  # "transcript_snippet" | "rule_evidence"
    text: Optional[str] = None
    start: Optional[float] = None
    end: Optional[float] = None
    rule_id: Optional[str] = None


class StepEvaluation(BaseModel):
    step_id: str
    passed: bool
    evidence: List[EvidenceItem] = []
    rationale: str


class LLMStageEvaluationResponse(BaseModel):
    """LLM stage evaluation response per Phase 4 spec"""
    evaluation_id: str
    flow_version_id: str
    recording_id: str
    stage_id: str
    stage_score: int = Field(..., ge=0, le=100)
    step_evaluations: List[StepEvaluation] = []
    stage_feedback: List[str] = []
    stage_confidence: float = Field(..., ge=0.0, le=1.0)
    critical_violation: bool = False
    notes: Optional[str] = None
    
    @validator('stage_score')
    def validate_score(cls, v):
        if not isinstance(v, int) or v < 0 or v > 100:
            raise ValueError('stage_score must be integer between 0 and 100')
        return v
    
    @validator('stage_confidence')
    def validate_confidence(cls, v):
        if not isinstance(v, (int, float)) or v < 0.0 or v > 1.0:
            raise ValueError('stage_confidence must be float between 0.0 and 1.0')
        return float(v)

