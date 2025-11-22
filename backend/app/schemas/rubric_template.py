"""
Phase 5: Rubric Template Schemas
Pydantic schemas for RubricTemplate CRUD operations.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal


class LevelDefinition(BaseModel):
    """Rubric level definition"""
    name: str
    min_score: int = Field(..., ge=0, le=100)
    max_score: int = Field(..., ge=0, le=100)
    description: Optional[str] = None
    label: Optional[str] = None
    
    @validator('max_score')
    def validate_max_score(cls, v, values):
        if 'min_score' in values and v < values['min_score']:
            raise ValueError('max_score must be >= min_score')
        return v


class RubricMappingCreate(BaseModel):
    target_type: str = Field(..., pattern="^(stage|step)$")
    target_id: str
    contribution_weight: float = Field(1.0, gt=0)
    required_flag: bool = False


class RubricMappingUpdate(BaseModel):
    contribution_weight: Optional[float] = Field(None, gt=0)
    required_flag: Optional[bool] = None


class RubricMappingResponse(BaseModel):
    id: str
    target_type: str
    target_id: str
    contribution_weight: float
    required_flag: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class RubricCategoryCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    weight: float = Field(..., gt=0, le=100)
    pass_threshold: int = Field(75, ge=0, le=100)
    level_definitions: Optional[List[LevelDefinition]] = []


class RubricCategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    weight: Optional[float] = Field(None, gt=0, le=100)
    pass_threshold: Optional[int] = Field(None, ge=0, le=100)
    level_definitions: Optional[List[LevelDefinition]] = None


class RubricCategoryResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    weight: float
    pass_threshold: int
    level_definitions: List[Dict[str, Any]]
    mappings: List[RubricMappingResponse] = []
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RubricTemplateCreate(BaseModel):
    flow_version_id: str
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    categories: Optional[List[RubricCategoryCreate]] = []


class RubricTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class RubricTemplateResponse(BaseModel):
    id: str
    flow_version_id: str
    version_number: int
    name: str
    description: Optional[str]
    is_active: bool
    created_by_user_id: str
    categories: List[RubricCategoryResponse] = []
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PreviewCalculationRequest(BaseModel):
    """Request for preview calculation with sample stage scores"""
    stage_scores: Dict[str, int] = Field(..., description="Map of stage_id to score (0-100)")


class PreviewCalculationResponse(BaseModel):
    """Preview calculation result"""
    category_scores: List[Dict[str, Any]]
    overall_score: int
    overall_passed: bool

