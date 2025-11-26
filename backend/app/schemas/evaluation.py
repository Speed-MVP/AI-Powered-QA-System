from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class StageScoreResponse(BaseModel):
    """Blueprint-based stage score"""
    stage_id: Optional[str] = None
    stage_name: Optional[str] = None
    name: Optional[str] = None
    score: int
    passed: Optional[bool] = None
    feedback: Optional[str] = None
    behaviors: Optional[List[Dict[str, Any]]] = None


class PolicyViolationResponse(BaseModel):
    """Blueprint-based policy violation"""
    type: str
    severity: str  # 'critical' | 'major' | 'minor'
    description: str
    rule_id: Optional[str] = None
    timestamp: Optional[float] = None


class EvaluationResponse(BaseModel):
    """Blueprint-based evaluation response"""
    evaluation_id: str
    recording_id: str
    blueprint_id: Optional[str] = None
    overall_score: int
    overall_passed: bool
    requires_human_review: bool
    confidence_score: Optional[float] = None
    stage_scores: List[StageScoreResponse] = []
    policy_violations: List[PolicyViolationResponse] = []
    created_at: str
    status: str
    
    class Config:
        from_attributes = True

