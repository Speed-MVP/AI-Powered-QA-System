"""
Phase 1: FlowVersion API Routes
CRUD operations for FlowVersion, Stages, and Steps.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.database import get_db
from app.models.user import User, UserRole
from app.models.flow_version import FlowVersion
from app.models.flow_stage import FlowStage
from app.models.flow_step import FlowStep
from app.middleware.auth import get_current_user
from app.middleware.permissions import require_company_access
from app.schemas.flow_version import (
    FlowVersionCreate,
    FlowVersionUpdate,
    FlowVersionResponse,
    FlowVersionJSON,
    StageCreate,
    StageUpdate,
    StageResponse,
    StepCreate,
    StepUpdate,
    StepResponse,
    ReorderStagesRequest,
    ReorderStepsRequest,
)
from app.services.flow_version_validator import FlowVersionValidator
from typing import List
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/flow-versions", tags=["flow-versions"])


@router.get("", response_model=List[FlowVersionResponse])
async def list_flow_versions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all FlowVersions for the user's company"""
    flow_versions = db.query(FlowVersion).filter(
        FlowVersion.company_id == current_user.company_id
    ).order_by(FlowVersion.created_at.desc()).all()
    
    return flow_versions


@router.post("", response_model=FlowVersionResponse)
async def create_flow_version(
    flow_version_data: FlowVersionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new FlowVersion (admin or qa_manager only)"""
    if current_user.role not in [UserRole.admin, UserRole.qa_manager]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Check for duplicate name
    existing = db.query(FlowVersion).filter(
        FlowVersion.company_id == current_user.company_id,
        FlowVersion.name == flow_version_data.name
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="FlowVersion with this name already exists")
    
    flow_version = FlowVersion(
        company_id=current_user.company_id,
        name=flow_version_data.name,
        description=flow_version_data.description,
        is_active=True,
        version_number=1
    )
    db.add(flow_version)
    db.commit()
    db.refresh(flow_version)
    
    return flow_version


@router.get("/{flow_version_id}", response_model=FlowVersionResponse)
async def get_flow_version(
    flow_version_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get FlowVersion by ID"""
    flow_version = db.query(FlowVersion).filter(
        FlowVersion.id == flow_version_id
    ).first()
    
    if not flow_version:
        raise HTTPException(status_code=404, detail="FlowVersion not found")
    
    require_company_access(flow_version.company_id, current_user)
    
    return flow_version


@router.put("/{flow_version_id}", response_model=FlowVersionResponse)
async def update_flow_version(
    flow_version_id: str,
    flow_version_data: FlowVersionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update FlowVersion (admin or qa_manager only)"""
    if current_user.role not in [UserRole.admin, UserRole.qa_manager]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    flow_version = db.query(FlowVersion).filter(
        FlowVersion.id == flow_version_id
    ).first()
    
    if not flow_version:
        raise HTTPException(status_code=404, detail="FlowVersion not found")
    
    require_company_access(flow_version.company_id, current_user)
    
    # Check for duplicate name if name is being changed
    if flow_version_data.name and flow_version_data.name != flow_version.name:
        existing = db.query(FlowVersion).filter(
            FlowVersion.company_id == current_user.company_id,
            FlowVersion.name == flow_version_data.name,
            FlowVersion.id != flow_version_id
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="FlowVersion with this name already exists")
    
    # Update fields
    if flow_version_data.name is not None:
        flow_version.name = flow_version_data.name
    if flow_version_data.description is not None:
        flow_version.description = flow_version_data.description
    if flow_version_data.is_active is not None:
        flow_version.is_active = flow_version_data.is_active
    
    db.commit()
    db.refresh(flow_version)
    
    return flow_version


@router.delete("/{flow_version_id}")
async def delete_flow_version(
    flow_version_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete FlowVersion (admin or qa_manager only)"""
    if current_user.role not in [UserRole.admin, UserRole.qa_manager]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    flow_version = db.query(FlowVersion).filter(
        FlowVersion.id == flow_version_id
    ).first()
    
    if not flow_version:
        raise HTTPException(status_code=404, detail="FlowVersion not found")
    
    require_company_access(flow_version.company_id, current_user)
    
    db.delete(flow_version)
    db.commit()
    
    return {"message": "FlowVersion deleted successfully"}


@router.get("/{flow_version_id}/json", response_model=FlowVersionJSON)
async def get_flow_version_json(
    flow_version_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get FlowVersion in Phase 1 JSON format"""
    flow_version = db.query(FlowVersion).filter(
        FlowVersion.id == flow_version_id
    ).first()
    
    if not flow_version:
        raise HTTPException(status_code=404, detail="FlowVersion not found")
    
    require_company_access(flow_version.company_id, current_user)
    
    return FlowVersionJSON.from_orm(flow_version)


# Stage endpoints
@router.post("/{flow_version_id}/stages", response_model=StageResponse)
async def create_stage(
    flow_version_id: str,
    stage_data: StageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add stage to FlowVersion"""
    if current_user.role not in [UserRole.admin, UserRole.qa_manager]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    flow_version = db.query(FlowVersion).filter(
        FlowVersion.id == flow_version_id
    ).first()
    
    if not flow_version:
        raise HTTPException(status_code=404, detail="FlowVersion not found")
    
    require_company_access(flow_version.company_id, current_user)
    
    # Validate stage name unique within FlowVersion
    existing = db.query(FlowStage).filter(
        FlowStage.flow_version_id == flow_version_id,
        FlowStage.name == stage_data.name
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Stage with this name already exists")
    
    stage = FlowStage(
        flow_version_id=flow_version_id,
        name=stage_data.name,
        order=stage_data.order
    )
    db.add(stage)
    db.commit()
    db.refresh(stage)
    
    return stage


@router.put("/{flow_version_id}/stages/{stage_id}", response_model=StageResponse)
async def update_stage(
    flow_version_id: str,
    stage_id: str,
    stage_data: StageUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update stage"""
    if current_user.role not in [UserRole.admin, UserRole.qa_manager]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    stage = db.query(FlowStage).filter(
        FlowStage.id == stage_id,
        FlowStage.flow_version_id == flow_version_id
    ).first()
    
    if not stage:
        raise HTTPException(status_code=404, detail="Stage not found")
    
    flow_version = db.query(FlowVersion).filter(FlowVersion.id == flow_version_id).first()
    require_company_access(flow_version.company_id, current_user)
    
    # Validate stage name unique if changing
    if stage_data.name and stage_data.name != stage.name:
        existing = db.query(FlowStage).filter(
            FlowStage.flow_version_id == flow_version_id,
            FlowStage.name == stage_data.name,
            FlowStage.id != stage_id
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Stage with this name already exists")
    
    if stage_data.name is not None:
        stage.name = stage_data.name
    if stage_data.order is not None:
        stage.order = stage_data.order
    
    db.commit()
    db.refresh(stage)
    
    return stage


@router.delete("/{flow_version_id}/stages/{stage_id}")
async def delete_stage(
    flow_version_id: str,
    stage_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete stage"""
    if current_user.role not in [UserRole.admin, UserRole.qa_manager]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    stage = db.query(FlowStage).filter(
        FlowStage.id == stage_id,
        FlowStage.flow_version_id == flow_version_id
    ).first()
    
    if not stage:
        raise HTTPException(status_code=404, detail="Stage not found")
    
    flow_version = db.query(FlowVersion).filter(FlowVersion.id == flow_version_id).first()
    require_company_access(flow_version.company_id, current_user)
    
    db.delete(stage)
    db.commit()
    
    return {"message": "Stage deleted successfully"}


@router.post("/{flow_version_id}/reorder-stages")
async def reorder_stages(
    flow_version_id: str,
    reorder_data: ReorderStagesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reorder stages"""
    if current_user.role not in [UserRole.admin, UserRole.qa_manager]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    flow_version = db.query(FlowVersion).filter(
        FlowVersion.id == flow_version_id
    ).first()
    
    if not flow_version:
        raise HTTPException(status_code=404, detail="FlowVersion not found")
    
    require_company_access(flow_version.company_id, current_user)
    
    # Get all stages for this FlowVersion
    stages = db.query(FlowStage).filter(
        FlowStage.flow_version_id == flow_version_id
    ).all()
    
    stage_dict = {s.id: s for s in stages}
    
    # Validate all stage_ids exist
    if len(reorder_data.stage_ids) != len(stages):
        raise HTTPException(status_code=400, detail="Must include all stages in reorder")
    
    for stage_id in reorder_data.stage_ids:
        if stage_id not in stage_dict:
            raise HTTPException(status_code=400, detail=f"Stage {stage_id} not found")
    
    # Update orders
    for order, stage_id in enumerate(reorder_data.stage_ids, start=1):
        stage_dict[stage_id].order = order
    
    db.commit()
    
    return {"message": "Stages reordered successfully"}


# Step endpoints
@router.post("/{flow_version_id}/stages/{stage_id}/steps", response_model=StepResponse)
async def create_step(
    flow_version_id: str,
    stage_id: str,
    step_data: StepCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add step to stage"""
    if current_user.role not in [UserRole.admin, UserRole.qa_manager]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    stage = db.query(FlowStage).filter(
        FlowStage.id == stage_id,
        FlowStage.flow_version_id == flow_version_id
    ).first()
    
    if not stage:
        raise HTTPException(status_code=404, detail="Stage not found")
    
    flow_version = db.query(FlowVersion).filter(FlowVersion.id == flow_version_id).first()
    require_company_access(flow_version.company_id, current_user)
    
    # Validate step name unique within stage
    existing = db.query(FlowStep).filter(
        FlowStep.stage_id == stage_id,
        FlowStep.name == step_data.name
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Step with this name already exists")
    
    # Convert timing_requirement to dict
    timing_req = None
    if step_data.timing_requirement and step_data.timing_requirement.enabled:
        timing_req = {
            "enabled": step_data.timing_requirement.enabled,
            "seconds": step_data.timing_requirement.seconds
        }
    
    step = FlowStep(
        stage_id=stage_id,
        name=step_data.name,
        description=step_data.description or '',  # Model requires non-null, so use empty string
        required=step_data.required,
        expected_phrases=step_data.expected_phrases or [],
        timing_requirement=timing_req,
        order=step_data.order
    )
    db.add(step)
    db.commit()
    db.refresh(step)
    
    return step


@router.put("/{flow_version_id}/stages/{stage_id}/steps/{step_id}", response_model=StepResponse)
async def update_step(
    flow_version_id: str,
    stage_id: str,
    step_id: str,
    step_data: StepUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update step"""
    if current_user.role not in [UserRole.admin, UserRole.qa_manager]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    step = db.query(FlowStep).filter(
        FlowStep.id == step_id,
        FlowStep.stage_id == stage_id
    ).first()
    
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")
    
    stage = db.query(FlowStage).filter(FlowStage.id == stage_id).first()
    flow_version = db.query(FlowVersion).filter(FlowVersion.id == flow_version_id).first()
    require_company_access(flow_version.company_id, current_user)
    
    # Validate step name unique if changing
    if step_data.name and step_data.name != step.name:
        existing = db.query(FlowStep).filter(
            FlowStep.stage_id == stage_id,
            FlowStep.name == step_data.name,
            FlowStep.id != step_id
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Step with this name already exists")
    
    if step_data.name is not None:
        step.name = step_data.name
    if step_data.description is not None:
        step.description = step_data.description or ''  # Use empty string if None provided
    if step_data.required is not None:
        step.required = step_data.required
    if step_data.expected_phrases is not None:
        step.expected_phrases = step_data.expected_phrases
    if step_data.timing_requirement is not None:
        if step_data.timing_requirement.enabled:
            step.timing_requirement = {
                "enabled": step_data.timing_requirement.enabled,
                "seconds": step_data.timing_requirement.seconds
            }
        else:
            step.timing_requirement = None
    if step_data.order is not None:
        step.order = step_data.order
    
    db.commit()
    db.refresh(step)
    
    return step


@router.delete("/{flow_version_id}/stages/{stage_id}/steps/{step_id}")
async def delete_step(
    flow_version_id: str,
    stage_id: str,
    step_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete step"""
    if current_user.role not in [UserRole.admin, UserRole.qa_manager]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    step = db.query(FlowStep).filter(
        FlowStep.id == step_id,
        FlowStep.stage_id == stage_id
    ).first()
    
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")
    
    flow_version = db.query(FlowVersion).filter(FlowVersion.id == flow_version_id).first()
    require_company_access(flow_version.company_id, current_user)
    
    db.delete(step)
    db.commit()
    
    return {"message": "Step deleted successfully"}


@router.post("/{flow_version_id}/stages/{stage_id}/reorder-steps")
async def reorder_steps(
    flow_version_id: str,
    stage_id: str,
    reorder_data: ReorderStepsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reorder steps within a stage"""
    if current_user.role not in [UserRole.admin, UserRole.qa_manager]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    stage = db.query(FlowStage).filter(
        FlowStage.id == stage_id,
        FlowStage.flow_version_id == flow_version_id
    ).first()
    
    if not stage:
        raise HTTPException(status_code=404, detail="Stage not found")
    
    flow_version = db.query(FlowVersion).filter(FlowVersion.id == flow_version_id).first()
    require_company_access(flow_version.company_id, current_user)
    
    # Get all steps for this stage
    steps = db.query(FlowStep).filter(FlowStep.stage_id == stage_id).all()
    
    step_dict = {s.id: s for s in steps}
    
    # Validate all step_ids exist
    if len(reorder_data.step_ids) != len(steps):
        raise HTTPException(status_code=400, detail="Must include all steps in reorder")
    
    for step_id in reorder_data.step_ids:
        if step_id not in step_dict:
            raise HTTPException(status_code=400, detail=f"Step {step_id} not found")
    
    # Update orders
    for order, step_id in enumerate(reorder_data.step_ids, start=1):
        step_dict[step_id].order = order
    
    db.commit()
    
    return {"message": "Steps reordered successfully"}

