from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from decimal import Decimal


class EvaluationCriteriaCreate(BaseModel):
    category_name: str
    weight: Decimal
    passing_score: int
    evaluation_prompt: str


class EvaluationCriteriaResponse(BaseModel):
    id: str
    category_name: str
    weight: Decimal
    passing_score: int
    evaluation_prompt: str
    created_at: datetime
    rubric_levels: list = []  # Will be populated with RubricLevelResponse
    
    class Config:
        from_attributes = True


class PolicyTemplateCreate(BaseModel):
    template_name: str
    description: Optional[str] = None
    is_active: bool = True
    criteria: List[EvaluationCriteriaCreate] = []


class PolicyTemplateResponse(BaseModel):
    id: str
    company_id: str
    template_name: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    criteria: List[EvaluationCriteriaResponse] = []
    
    class Config:
        from_attributes = True

