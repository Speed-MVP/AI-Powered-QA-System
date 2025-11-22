"""
Phase 5: Rubric Template API Routes
CRUD operations for RubricTemplates, Categories, and Mappings.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.database import get_db
from app.models.user import User, UserRole
from app.models.rubric_template import RubricTemplate, RubricCategory, RubricMapping
from app.models.flow_version import FlowVersion
from app.middleware.auth import get_current_user
from app.middleware.permissions import require_company_access
from app.schemas.rubric_template import (
    RubricTemplateCreate,
    RubricTemplateUpdate,
    RubricTemplateResponse,
    RubricCategoryCreate,
    RubricCategoryUpdate,
    RubricCategoryResponse,
    RubricMappingCreate,
    RubricMappingUpdate,
    RubricMappingResponse,
    PreviewCalculationRequest,
    PreviewCalculationResponse,
)
from app.services.rubric_validator import RubricValidator
from app.services.rubric_scorer import RubricScorer
from typing import List, Optional
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/rubrics", tags=["rubrics"])


@router.get("", response_model=List[RubricTemplateResponse])
async def list_rubrics(
    flow_version_id: Optional[str] = Query(None, description="Filter by FlowVersion ID"),
    active_only: bool = Query(False, description="Show only active rubrics"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List RubricTemplates for the user's company"""
    query = db.query(RubricTemplate).join(FlowVersion).filter(
        FlowVersion.company_id == current_user.company_id
    )
    
    if flow_version_id:
        query = query.filter(RubricTemplate.flow_version_id == flow_version_id)
    
    
    if active_only:
        query = query.filter(RubricTemplate.is_active == True)
    
    rubrics = query.order_by(RubricTemplate.created_at.desc()).all()
    
    return rubrics


@router.post("", response_model=RubricTemplateResponse)
async def create_rubric(
    rubric_data: RubricTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new RubricTemplate (admin or qa_manager only)"""
    if current_user.role not in [UserRole.admin, UserRole.qa_manager]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Get FlowVersion and verify access
    flow_version = db.query(FlowVersion).filter(
        FlowVersion.id == rubric_data.flow_version_id
    ).first()
    
    if not flow_version:
        raise HTTPException(status_code=404, detail="FlowVersion not found")
    
    require_company_access(flow_version.company_id, current_user)
    
    # Create rubric template
    rubric = RubricTemplate(
        flow_version_id=rubric_data.flow_version_id,
        name=rubric_data.name,
        description=rubric_data.description,
        version_number=1,
        is_active=False,
        created_by_user_id=current_user.id
    )
    db.add(rubric)
    db.flush()
    
    # Create categories if provided
    if rubric_data.categories:
        total_weight = sum(c.weight for c in rubric_data.categories)
        if abs(total_weight - 100.0) > 0.01:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"Category weights must sum to 100. Current sum: {total_weight}"
            )
        
        for cat_data in rubric_data.categories:
            category = RubricCategory(
                rubric_template_id=rubric.id,
                name=cat_data.name,
                description=cat_data.description,
                weight=Decimal(str(cat_data.weight)),
                pass_threshold=cat_data.pass_threshold,
                level_definitions=cat_data.level_definitions or []
            )
            db.add(category)
    
    db.commit()
    db.refresh(rubric)
    
    return rubric


@router.get("/{rubric_id}", response_model=RubricTemplateResponse)
async def get_rubric(
    rubric_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get RubricTemplate by ID"""
    rubric = db.query(RubricTemplate).filter(RubricTemplate.id == rubric_id).first()
    
    if not rubric:
        raise HTTPException(status_code=404, detail="RubricTemplate not found")
    
    flow_version = db.query(FlowVersion).filter(FlowVersion.id == rubric.flow_version_id).first()
    require_company_access(flow_version.company_id, current_user)
    
    return rubric


@router.put("/{rubric_id}", response_model=RubricTemplateResponse)
async def update_rubric(
    rubric_id: str,
    rubric_data: RubricTemplateUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update RubricTemplate (admin or qa_manager only)"""
    if current_user.role not in [UserRole.admin, UserRole.qa_manager]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    rubric = db.query(RubricTemplate).filter(RubricTemplate.id == rubric_id).first()
    
    if not rubric:
        raise HTTPException(status_code=404, detail="RubricTemplate not found")
    
    flow_version = db.query(FlowVersion).filter(FlowVersion.id == rubric.flow_version_id).first()
    require_company_access(flow_version.company_id, current_user)
    
    if rubric_data.name is not None:
        rubric.name = rubric_data.name
    if rubric_data.description is not None:
        rubric.description = rubric_data.description
    if rubric_data.is_active is not None:
        rubric.is_active = rubric_data.is_active
    
    db.commit()
    db.refresh(rubric)
    
    return rubric


@router.delete("/{rubric_id}")
async def delete_rubric(
    rubric_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete RubricTemplate (admin or qa_manager only)"""
    if current_user.role not in [UserRole.admin, UserRole.qa_manager]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    rubric = db.query(RubricTemplate).filter(RubricTemplate.id == rubric_id).first()
    
    if not rubric:
        raise HTTPException(status_code=404, detail="RubricTemplate not found")
    
    flow_version = db.query(FlowVersion).filter(FlowVersion.id == rubric.flow_version_id).first()
    require_company_access(flow_version.company_id, current_user)
    
    db.delete(rubric)
    db.commit()
    
    return {"message": "RubricTemplate deleted successfully"}


@router.post("/{rubric_id}/categories", response_model=RubricCategoryResponse)
async def create_category(
    rubric_id: str,
    category_data: RubricCategoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add category to RubricTemplate"""
    if current_user.role not in [UserRole.admin, UserRole.qa_manager]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    rubric = db.query(RubricTemplate).filter(RubricTemplate.id == rubric_id).first()
    
    if not rubric:
        raise HTTPException(status_code=404, detail="RubricTemplate not found")
    
    flow_version = db.query(FlowVersion).filter(FlowVersion.id == rubric.flow_version_id).first()
    require_company_access(flow_version.company_id, current_user)
    
    # Validate level definitions
    if category_data.level_definitions:
        is_valid, errors = RubricValidator.validate_level_definitions(
            [ld.dict() for ld in category_data.level_definitions]
        )
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid level definitions: {', '.join(errors)}")
    
    category = RubricCategory(
        rubric_template_id=rubric_id,
        name=category_data.name,
        description=category_data.description,
        weight=Decimal(str(category_data.weight)),
        pass_threshold=category_data.pass_threshold,
        level_definitions=[ld.dict() for ld in category_data.level_definitions] if category_data.level_definitions else []
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    
    return category


@router.put("/{rubric_id}/categories/{category_id}", response_model=RubricCategoryResponse)
async def update_category(
    rubric_id: str,
    category_id: str,
    category_data: RubricCategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update category"""
    if current_user.role not in [UserRole.admin, UserRole.qa_manager]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    category = db.query(RubricCategory).filter(
        RubricCategory.id == category_id,
        RubricCategory.rubric_template_id == rubric_id
    ).first()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    rubric = db.query(RubricTemplate).filter(RubricTemplate.id == rubric_id).first()
    flow_version = db.query(FlowVersion).filter(FlowVersion.id == rubric.flow_version_id).first()
    require_company_access(flow_version.company_id, current_user)
    
    if category_data.name is not None:
        category.name = category_data.name
    if category_data.description is not None:
        category.description = category_data.description
    if category_data.weight is not None:
        category.weight = Decimal(str(category_data.weight))
    if category_data.pass_threshold is not None:
        category.pass_threshold = category_data.pass_threshold
    if category_data.level_definitions is not None:
        # Validate level definitions
        is_valid, errors = RubricValidator.validate_level_definitions(
            [ld.dict() for ld in category_data.level_definitions]
        )
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid level definitions: {', '.join(errors)}")
        category.level_definitions = [ld.dict() for ld in category_data.level_definitions]
    
    db.commit()
    db.refresh(category)
    
    return category


@router.delete("/{rubric_id}/categories/{category_id}")
async def delete_category(
    rubric_id: str,
    category_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete category"""
    if current_user.role not in [UserRole.admin, UserRole.qa_manager]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    category = db.query(RubricCategory).filter(
        RubricCategory.id == category_id,
        RubricCategory.rubric_template_id == rubric_id
    ).first()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    rubric = db.query(RubricTemplate).filter(RubricTemplate.id == rubric_id).first()
    flow_version = db.query(FlowVersion).filter(FlowVersion.id == rubric.flow_version_id).first()
    require_company_access(flow_version.company_id, current_user)
    
    db.delete(category)
    db.commit()
    
    return {"message": "Category deleted successfully"}


@router.post("/{rubric_id}/categories/{category_id}/mappings", response_model=RubricMappingResponse)
async def create_mapping(
    rubric_id: str,
    category_id: str,
    mapping_data: RubricMappingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add mapping to category"""
    if current_user.role not in [UserRole.admin, UserRole.qa_manager]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    category = db.query(RubricCategory).filter(
        RubricCategory.id == category_id,
        RubricCategory.rubric_template_id == rubric_id
    ).first()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    rubric = db.query(RubricTemplate).filter(RubricTemplate.id == rubric_id).first()
    flow_version = db.query(FlowVersion).filter(FlowVersion.id == rubric.flow_version_id).first()
    require_company_access(flow_version.company_id, current_user)
    
    # Validate target exists
    if mapping_data.target_type == "stage":
        if not any(s.id == mapping_data.target_id for s in flow_version.stages):
            raise HTTPException(status_code=400, detail=f"Stage {mapping_data.target_id} not found in FlowVersion")
    elif mapping_data.target_type == "step":
        all_step_ids = []
        for stage in flow_version.stages:
            for step in stage.steps:
                all_step_ids.append(step.id)
        if mapping_data.target_id not in all_step_ids:
            raise HTTPException(status_code=400, detail=f"Step {mapping_data.target_id} not found in FlowVersion")
    
    mapping = RubricMapping(
        rubric_category_id=category_id,
        target_type=mapping_data.target_type,
        target_id=mapping_data.target_id,
        contribution_weight=Decimal(str(mapping_data.contribution_weight)),
        required_flag=mapping_data.required_flag
    )
    db.add(mapping)
    db.commit()
    db.refresh(mapping)
    
    return mapping


@router.delete("/{rubric_id}/categories/{category_id}/mappings/{mapping_id}")
async def delete_mapping(
    rubric_id: str,
    category_id: str,
    mapping_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete mapping"""
    if current_user.role not in [UserRole.admin, UserRole.qa_manager]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    mapping = db.query(RubricMapping).filter(
        RubricMapping.id == mapping_id,
        RubricMapping.rubric_category_id == category_id
    ).first()
    
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
    
    category = db.query(RubricCategory).filter(RubricCategory.id == category_id).first()
    rubric = db.query(RubricTemplate).filter(RubricTemplate.id == rubric_id).first()
    flow_version = db.query(FlowVersion).filter(FlowVersion.id == rubric.flow_version_id).first()
    require_company_access(flow_version.company_id, current_user)
    
    db.delete(mapping)
    db.commit()
    
    return {"message": "Mapping deleted successfully"}


@router.post("/{rubric_id}/publish")
async def publish_rubric(
    rubric_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Publish RubricTemplate (validate and activate)"""
    if current_user.role not in [UserRole.admin, UserRole.qa_manager]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    rubric = db.query(RubricTemplate).filter(RubricTemplate.id == rubric_id).first()
    
    if not rubric:
        raise HTTPException(status_code=404, detail="RubricTemplate not found")
    
    flow_version = db.query(FlowVersion).filter(FlowVersion.id == rubric.flow_version_id).first()
    require_company_access(flow_version.company_id, current_user)
    
    # Validate rubric
    is_valid, errors = RubricValidator.validate_rubric_template(rubric, flow_version)
    
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Rubric validation failed: {', '.join(errors)}")
    
    # Deactivate other active rubrics for this FlowVersion
    db.query(RubricTemplate).filter(
        RubricTemplate.flow_version_id == rubric.flow_version_id,
        RubricTemplate.id != rubric_id,
        RubricTemplate.is_active == True
    ).update({"is_active": False})
    
    # Activate this rubric
    rubric.is_active = True
    db.commit()
    db.refresh(rubric)
    
    return {"message": "RubricTemplate published successfully", "rubric": RubricTemplateResponse.from_orm(rubric)}


@router.post("/{rubric_id}/preview", response_model=PreviewCalculationResponse)
async def preview_calculation(
    rubric_id: str,
    preview_data: PreviewCalculationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Preview calculation with sample stage scores"""
    rubric = db.query(RubricTemplate).filter(RubricTemplate.id == rubric_id).first()
    
    if not rubric:
        raise HTTPException(status_code=404, detail="RubricTemplate not found")
    
    flow_version = db.query(FlowVersion).filter(FlowVersion.id == rubric.flow_version_id).first()
    require_company_access(flow_version.company_id, current_user)
    
    # Create mock LLM stage evaluations
    llm_stage_evaluations = {
        stage_id: {
            "stage_score": score,
            "stage_confidence": 0.9,
            "critical_violation": False
        }
        for stage_id, score in preview_data.stage_scores.items()
    }
    
    # Use RubricScorer to calculate
    scorer = RubricScorer()
    result = scorer.score(
        rubric,
        llm_stage_evaluations,
        {"rule_evaluations": []}  # Empty deterministic result for preview
    )
    
    return PreviewCalculationResponse(
        category_scores=result["category_scores"],
        overall_score=result["overall_score"],
        overall_passed=result["overall_passed"]
    )

