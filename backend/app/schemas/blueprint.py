"""
Blueprint Pydantic Schemas - Phase 2
Schemas for Blueprint JSON payload (API requests/responses)
"""

from pydantic import BaseModel, Field, field_validator, model_serializer, field_serializer
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
import enum


# Enums matching models
class BehaviorType(str, enum.Enum):
    required = "required"
    optional = "optional"
    forbidden = "forbidden"
    critical = "critical"


class DetectionMode(str, enum.Enum):
    semantic = "semantic"
    exact_phrase = "exact_phrase"
    hybrid = "hybrid"


class CriticalAction(str, enum.Enum):
    fail_stage = "fail_stage"
    fail_overall = "fail_overall"
    flag_only = "flag_only"


class BlueprintStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    archived = "archived"


# Behavior Schemas
class BehaviorBase(BaseModel):
    behavior_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    behavior_type: BehaviorType = BehaviorType.required
    detection_mode: DetectionMode = DetectionMode.semantic
    phrases: Optional[List[str]] = None
    weight: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    critical_action: Optional[CriticalAction] = None
    metadata: Optional[Dict[str, Any]] = None

    @field_validator('phrases')
    @classmethod
    def validate_phrases(cls, v, info):
        if info.data.get('detection_mode') != 'semantic' and (not v or len(v) == 0):
            raise ValueError('phrases must be provided when detection_mode is not semantic')
        return v

    @field_validator('critical_action')
    @classmethod
    def validate_critical_action(cls, v, info):
        if info.data.get('behavior_type') == 'critical' and not v:
            raise ValueError('critical_action is required when behavior_type is critical')
        return v


class BehaviorCreate(BehaviorBase):
    ui_order: Optional[int] = 0


class BehaviorUpdate(BaseModel):
    behavior_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    behavior_type: Optional[BehaviorType] = None
    detection_mode: Optional[DetectionMode] = None
    phrases: Optional[List[str]] = None
    weight: Optional[Decimal] = Field(None, ge=0, le=100)
    critical_action: Optional[CriticalAction] = None
    metadata: Optional[Dict[str, Any]] = None
    ui_order: Optional[int] = None


class BehaviorResponse(BehaviorBase):
    id: str
    stage_id: str
    ui_order: int
    created_at: datetime
    updated_at: datetime
    # Override metadata to read from extra_metadata attribute
    metadata: Optional[Dict[str, Any]] = Field(None, alias="extra_metadata")

    class Config:
        from_attributes = True
        populate_by_name = True


# Stage Schemas
class StageBase(BaseModel):
    stage_name: str = Field(..., min_length=1, max_length=150)
    ordering_index: int = Field(..., ge=1)
    stage_weight: Optional[Decimal] = Field(None, ge=0, le=100)
    metadata: Optional[Dict[str, Any]] = None


class StageCreate(StageBase):
    behaviors: Optional[List[BehaviorCreate]] = []


class StageUpdate(BaseModel):
    stage_name: Optional[str] = Field(None, min_length=1, max_length=150)
    ordering_index: Optional[int] = Field(None, ge=1)
    stage_weight: Optional[Decimal] = Field(None, ge=0, le=100)
    metadata: Optional[Dict[str, Any]] = None


class StageResponse(StageBase):
    id: str
    blueprint_id: str
    behaviors: List[BehaviorResponse] = []
    created_at: datetime
    updated_at: datetime
    # Override metadata to read from extra_metadata attribute
    metadata: Optional[Dict[str, Any]] = Field(None, alias="extra_metadata")

    class Config:
        from_attributes = True
        populate_by_name = True


# Blueprint Schemas
class BlueprintBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BlueprintCreate(BlueprintBase):
    stages: List[StageCreate] = Field(default_factory=list)

    @field_validator('stages')
    @classmethod
    def validate_stages(cls, v):
        # Allow empty stages array - stages can be added later
        if not v:
            return []
        # Validate unique ordering_index if stages are provided
        ordering_indices = [stage.ordering_index for stage in v]
        if len(ordering_indices) != len(set(ordering_indices)):
            raise ValueError('ordering_index must be unique within blueprint')
        return v


class BlueprintUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    stages: Optional[List[StageCreate]] = None


class BlueprintResponse(BlueprintBase):
    id: str
    company_id: str
    status: BlueprintStatus
    version_number: int
    compiled_flow_version_id: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    stages: List[StageResponse] = []
    stages_count: Optional[int] = None
    # Override metadata to read from extra_metadata attribute
    metadata: Optional[Dict[str, Any]] = Field(None, alias="extra_metadata")

    class Config:
        from_attributes = True
        populate_by_name = True


class BlueprintListResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    status: BlueprintStatus
    version_number: int
    stages_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Version Schemas
class BlueprintVersionResponse(BaseModel):
    id: str
    blueprint_id: str
    version_number: int
    snapshot: Dict[str, Any]
    compiled_flow_version_id: Optional[str] = None
    published_by: Optional[str] = None
    published_at: datetime

    class Config:
        from_attributes = True


# Publish Schemas
class PublishRequest(BaseModel):
    force_normalize_weights: bool = False
    publish_note: Optional[str] = None
    compiler_options: Optional[Dict[str, Any]] = None


class PublishResponse(BaseModel):
    job_id: str
    blueprint_id: str
    status: str  # queued, running, succeeded, failed
    links: Dict[str, str]


class PublishStatusResponse(BaseModel):
    job_id: str
    status: str  # queued, running, succeeded, failed
    progress: Optional[int] = None
    compiled_flow_version_id: Optional[str] = None
    errors: Optional[List[Dict[str, Any]]] = None
    warnings: Optional[List[Dict[str, Any]]] = None


# Duplicate Schema
class BlueprintDuplicateRequest(BaseModel):
    name: Optional[str] = None  # If not provided, will append " (Copy)" to original name


# Export/Import Schemas
class BlueprintExportResponse(BaseModel):
    blueprint: Dict[str, Any]
    exported_at: datetime


class BlueprintImportRequest(BaseModel):
    blueprint_json: Dict[str, Any]
    name: Optional[str] = None  # Override name if provided

