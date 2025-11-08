from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class CategoryScoreResponse(BaseModel):
    id: str
    category_name: str
    score: int
    feedback: Optional[str] = None
    
    class Config:
        from_attributes = True


class PolicyViolationResponse(BaseModel):
    id: str
    violation_type: str
    description: str
    severity: str
    criteria_id: str
    
    class Config:
        from_attributes = True


class CustomerToneResponse(BaseModel):
    primary_emotion: str
    confidence: float
    description: str
    emotional_journey: Optional[List[Dict[str, Any]]] = None


class EvaluationResponse(BaseModel):
    id: str
    recording_id: str
    policy_template_id: str
    overall_score: int
    resolution_detected: bool
    resolution_confidence: float
    customer_tone: Optional[CustomerToneResponse] = None
    llm_analysis: Dict[str, Any]
    status: str
    created_at: datetime
    category_scores: List[CategoryScoreResponse] = []
    policy_violations: List[PolicyViolationResponse] = []
    
    class Config:
        from_attributes = True

