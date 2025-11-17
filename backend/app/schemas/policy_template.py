from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from app.schemas.rubric_level import RubricLevelResponse


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
    rubric_levels: List[RubricLevelResponse] = []
    
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
    policy_rules: Optional[dict] = None
    policy_rules_version: Optional[int] = None
    enable_structured_rules: bool = False
    
    class Config:
        from_attributes = True

