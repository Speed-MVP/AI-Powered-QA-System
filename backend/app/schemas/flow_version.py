"""
Phase 1: FlowVersion Schemas
Pydantic schemas for FlowVersion CRUD operations matching Phase 1 JSON structure.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime


class TimingRequirement(BaseModel):
    enabled: bool = False
    seconds: Optional[float] = None
    
    @validator('seconds')
    def validate_seconds(cls, v, values):
        if values.get('enabled') and (v is None or v <= 0):
            raise ValueError('seconds must be positive when timing requirement is enabled')
        return v
    
    class Config:
        # Allow None for the entire object
        allow_none = True


class StepCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    required: bool = False
    expected_phrases: Optional[List[str]] = []
    timing_requirement: Optional[TimingRequirement] = None
    order: int = Field(..., ge=1)


class StepUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = Field(None, min_length=1)
    required: Optional[bool] = None
    expected_phrases: Optional[List[str]] = None
    timing_requirement: Optional[TimingRequirement] = None
    order: Optional[int] = Field(None, ge=1)


class StepResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    required: bool
    expected_phrases: List[str]
    timing_requirement: Optional[Dict[str, Any]] = None
    order: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class StageCreate(BaseModel):
    name: str = Field(..., min_length=1)
    order: int = Field(..., ge=1)


class StageUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    order: Optional[int] = Field(None, ge=1)


class StageResponse(BaseModel):
    id: str
    name: str
    order: int
    steps: List[StepResponse] = []
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class FlowVersionCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None


class FlowVersionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class FlowVersionResponse(BaseModel):
    id: str
    company_id: str
    name: str
    description: Optional[str]
    is_active: bool
    version_number: int
    stages: List[StageResponse] = []
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Phase 1 spec JSON structure
class FlowVersionJSON(BaseModel):
    """Matches Phase 1 spec FlowVersion JSON structure"""
    id: str
    name: str
    stages: List[Dict[str, Any]]
    
    class Config:
        from_attributes = True
    
    @classmethod
    def from_orm(cls, flow_version):
        """Convert FlowVersion ORM object to Phase 1 JSON structure"""
        stages_data = []
        for stage in sorted(flow_version.stages, key=lambda s: s.order):
            steps_data = []
            for step in sorted(stage.steps, key=lambda s: s.order):
                step_data = {
                    "id": step.id,
                    "name": step.name,
                    "description": step.description,
                    "required": step.required,
                    "expected_phrases": step.expected_phrases or [],
                    "timing_requirement": step.timing_requirement or {"enabled": False, "seconds": None},
                    "order": step.order
                }
                steps_data.append(step_data)
            
            stage_data = {
                "id": stage.id,
                "name": stage.name,
                "order": stage.order,
                "steps": steps_data
            }
            stages_data.append(stage_data)
        
        return cls(
            id=flow_version.id,
            name=flow_version.name,
            stages=stages_data
        )


class ReorderStagesRequest(BaseModel):
    stage_ids: List[str] = Field(..., min_items=1)


class ReorderStepsRequest(BaseModel):
    step_ids: List[str] = Field(..., min_items=1)

