"""
Blueprint API Routes - Phase 3
Complete CRUD, publish, sandbox, and management endpoints for QA Blueprints
"""

from fastapi import APIRouter, Depends, HTTPException, Header, Request, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from typing import List, Optional, Dict, Any
import logging
import hashlib
import json
from datetime import datetime

from app.database import get_db
from app.models.user import User, UserRole
from app.models.qa_blueprint import QABlueprint, BlueprintStatus
from app.models.qa_blueprint_stage import QABlueprintStage
from app.models.qa_blueprint_behavior import QABlueprintBehavior
from app.models.qa_blueprint_version import QABlueprintVersion
from app.models.qa_blueprint_compiler_map import QABlueprintCompilerMap
from app.models.qa_blueprint_audit_log import QABlueprintAuditLog, ChangeType
from app.middleware.auth import get_current_user
from app.middleware.permissions import require_company_access
from app.schemas.blueprint import (
    BlueprintCreate,
    BlueprintUpdate,
    BlueprintResponse,
    BlueprintListResponse,
    StageCreate,
    StageUpdate,
    StageResponse,
    BehaviorCreate,
    BehaviorUpdate,
    BehaviorResponse,
    BlueprintVersionResponse,
    PublishRequest,
    PublishResponse,
    PublishStatusResponse,
    BlueprintDuplicateRequest,
    BlueprintExportResponse,
    BlueprintImportRequest,
)
from app.services.blueprint_validator import BlueprintValidator
from app.services.cloud_tasks import cloud_tasks_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/blueprints", tags=["blueprints"])

# Note: Sandbox endpoints are in routes/sandbox.py

validator = BlueprintValidator()


def compute_etag(blueprint: QABlueprint) -> str:
    """Compute ETag for blueprint"""
    content = f"{blueprint.id}{blueprint.updated_at.isoformat()}{blueprint.version_number}"
    return hashlib.md5(content.encode()).hexdigest()


# ==================== Blueprint CRUD ====================

@router.post("", response_model=BlueprintResponse, status_code=201)
async def create_blueprint(
    blueprint_data: BlueprintCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    """Create new blueprint (draft) - admin or qa_manager only"""
    logger.debug(f"Creating blueprint: name={blueprint_data.name}, stages={len(blueprint_data.stages)}")
    if current_user.role not in [UserRole.admin, UserRole.qa_manager]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Check for duplicate name
    existing = db.query(QABlueprint).filter(
        QABlueprint.company_id == current_user.company_id,
        QABlueprint.name == blueprint_data.name
    ).first()
    
    if existing:
        raise HTTPException(status_code=409, detail="Blueprint with this name already exists")
    
    # Create blueprint
    blueprint = QABlueprint(
        company_id=current_user.company_id,
        name=blueprint_data.name,
        description=blueprint_data.description,
        status=BlueprintStatus.draft,
        version_number=1,
        created_by=current_user.id,
        updated_by=current_user.id,
        extra_metadata=blueprint_data.metadata
    )
    db.add(blueprint)
    db.flush()
    
    # Create stages and behaviors
    for stage_data in blueprint_data.stages:
        stage = QABlueprintStage(
            blueprint_id=blueprint.id,
            stage_name=stage_data.stage_name,
            ordering_index=stage_data.ordering_index,
            stage_weight=stage_data.stage_weight,
            extra_metadata=stage_data.metadata
        )
        db.add(stage)
        db.flush()
        
        for behavior_data in stage_data.behaviors:
            behavior = QABlueprintBehavior(
                stage_id=stage.id,
                behavior_name=behavior_data.behavior_name,
                description=behavior_data.description,
                behavior_type=behavior_data.behavior_type,
                detection_mode=behavior_data.detection_mode,
                phrases=behavior_data.phrases,
                weight=behavior_data.weight,
                critical_action=behavior_data.critical_action,
                ui_order=behavior_data.ui_order or 0,
                extra_metadata=behavior_data.metadata
            )
            db.add(behavior)
    
    # Create audit log
    audit_log = QABlueprintAuditLog(
        blueprint_id=blueprint.id,
        changed_by=current_user.id,
        change_type=ChangeType.create,
        change_summary=f"Created blueprint '{blueprint.name}'"
    )
    db.add(audit_log)
    
    db.commit()
    db.refresh(blueprint)
    
    response = BlueprintResponse.model_validate(blueprint)
    response.stages_count = len(blueprint.stages)
    return response


@router.get("", response_model=List[BlueprintListResponse])
async def list_blueprints(
    status: Optional[BlueprintStatus] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List blueprints for the user's company (paginated)"""
    try:
        logger.info(f"Listing blueprints for user_id={current_user.id}, company_id={current_user.company_id}, status={status}, skip={skip}, limit={limit}")
        
        # Debug: Check total blueprints in database
        total_blueprints = db.query(QABlueprint).count()
        logger.info(f"Total blueprints in database: {total_blueprints}")
        
        # Debug: Check blueprints for this company
        company_blueprints_count = db.query(QABlueprint).filter(
            QABlueprint.company_id == current_user.company_id
        ).count()
        logger.info(f"Blueprints for company_id={current_user.company_id}: {company_blueprints_count}")
        
        # Debug: List all company_ids to see what's in the database
        all_company_ids = db.query(QABlueprint.company_id).distinct().all()
        logger.info(f"All company_ids in blueprints table: {[c[0] for c in all_company_ids]}")
        
        query = db.query(QABlueprint).filter(
            QABlueprint.company_id == current_user.company_id
        )
        
        if status:
            query = query.filter(QABlueprint.status == status)
        
        blueprints = query.order_by(QABlueprint.updated_at.desc()).offset(skip).limit(limit).all()
        logger.info(f"Found {len(blueprints)} blueprints after filtering")
        
        # If no blueprints found for this company but blueprints exist, log a warning
        if len(blueprints) == 0 and total_blueprints > 0:
            logger.warning(f"WARNING: No blueprints found for company_id={current_user.company_id}, but {total_blueprints} blueprints exist in database!")
            logger.warning(f"User's company_id: {current_user.company_id}")
            logger.warning(f"Available company_ids: {[c[0] for c in all_company_ids]}")
        
        result = []
        for bp in blueprints:
            try:
                # Get stages count using a count query to avoid lazy loading
                stages_count = db.query(QABlueprintStage).filter(
                    QABlueprintStage.blueprint_id == bp.id
                ).count()
                
                # Manually construct response to avoid serialization issues
                item = BlueprintListResponse(
                    id=bp.id,
                    name=bp.name,
                    description=bp.description,
                    status=bp.status,
                    version_number=bp.version_number,
                    stages_count=stages_count,
                    created_at=bp.created_at,
                    updated_at=bp.updated_at
                )
                result.append(item)
                logger.info(f"Successfully serialized blueprint {bp.id}: {bp.name}, stages={stages_count}")
            except Exception as e:
                logger.error(f"Error serializing blueprint {bp.id} ({bp.name}): {e}", exc_info=True)
                import traceback
                logger.error(traceback.format_exc())
                # Skip this blueprint and continue with others
                continue
        
        logger.info(f"Returning {len(result)} blueprints out of {len(blueprints)} found")
        return result
    except Exception as e:
        logger.error(f"Error listing blueprints: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error listing blueprints: {str(e)}")


@router.get("/{blueprint_id}", response_model=BlueprintResponse)
async def get_blueprint(
    blueprint_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get blueprint by ID with stages and behaviors"""
    # Eager load stages and behaviors to avoid N+1 queries
    blueprint = db.query(QABlueprint).options(
        joinedload(QABlueprint.stages).joinedload(QABlueprintStage.behaviors)
    ).filter(
        QABlueprint.id == blueprint_id
    ).first()
    
    if not blueprint:
        raise HTTPException(status_code=404, detail="Blueprint not found")
    
    require_company_access(blueprint.company_id, current_user)
    
    response = BlueprintResponse.model_validate(blueprint)
    response.stages_count = len(blueprint.stages)
    # Convert extra_metadata to metadata in response
    if hasattr(response, 'metadata') and response.metadata is None and hasattr(blueprint, 'extra_metadata'):
        response.metadata = blueprint.extra_metadata
    
    # Set ETag header
    from fastapi.responses import Response
    etag = compute_etag(blueprint)
    
    return response


@router.put("/{blueprint_id}", response_model=BlueprintResponse)
async def update_blueprint(
    blueprint_id: str,
    blueprint_data: BlueprintUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    if_match: Optional[str] = Header(None, alias="If-Match"),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    """Update blueprint (draft only) - with ETag concurrency control"""
    blueprint = db.query(QABlueprint).filter(
        QABlueprint.id == blueprint_id
    ).first()
    
    if not blueprint:
        raise HTTPException(status_code=404, detail="Blueprint not found")
    
    require_company_access(blueprint.company_id, current_user)
    
    if current_user.role not in [UserRole.admin, UserRole.qa_manager]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Only draft blueprints can be updated
    if blueprint.status != BlueprintStatus.draft:
        raise HTTPException(status_code=403, detail="Only draft blueprints can be updated")
    
    # ETag check
    if if_match:
        current_etag = compute_etag(blueprint)
        if if_match != current_etag:
            raise HTTPException(
                status_code=409,
                detail="Blueprint was modified by another user",
                headers={"ETag": current_etag}
            )
    
    # Update fields
    if blueprint_data.name is not None:
        # Check for duplicate name
        existing = db.query(QABlueprint).filter(
            QABlueprint.company_id == current_user.company_id,
            QABlueprint.name == blueprint_data.name,
            QABlueprint.id != blueprint_id
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="Blueprint with this name already exists")
        blueprint.name = blueprint_data.name
    
    if blueprint_data.description is not None:
        blueprint.description = blueprint_data.description
    
    if blueprint_data.metadata is not None:
        blueprint.extra_metadata = blueprint_data.metadata
    
    blueprint.updated_by = current_user.id
    
    # Update stages if provided
    if blueprint_data.stages is not None:
        # Delete existing stages (cascade will delete behaviors)
        db.query(QABlueprintStage).filter(
            QABlueprintStage.blueprint_id == blueprint_id
        ).delete()
        
        # Create new stages
        for stage_data in blueprint_data.stages:
            stage = QABlueprintStage(
                blueprint_id=blueprint.id,
                stage_name=stage_data.stage_name,
                ordering_index=stage_data.ordering_index,
                stage_weight=stage_data.stage_weight,
                extra_metadata=stage_data.metadata
            )
            db.add(stage)
            db.flush()
            
            for behavior_data in stage_data.behaviors:
                behavior = QABlueprintBehavior(
                    stage_id=stage.id,
                    behavior_name=behavior_data.behavior_name,
                    description=behavior_data.description,
                    behavior_type=behavior_data.behavior_type,
                    detection_mode=behavior_data.detection_mode,
                    phrases=behavior_data.phrases,
                    weight=behavior_data.weight,
                    critical_action=behavior_data.critical_action,
                    ui_order=behavior_data.ui_order or 0,
                    extra_metadata=behavior_data.metadata
                )
                db.add(behavior)
    
    # Create audit log
    audit_log = QABlueprintAuditLog(
        blueprint_id=blueprint.id,
        changed_by=current_user.id,
        change_type=ChangeType.update,
        change_summary=f"Updated blueprint '{blueprint.name}'"
    )
    db.add(audit_log)
    
    db.commit()
    db.refresh(blueprint)
    
    response = BlueprintResponse.model_validate(blueprint)
    response.stages_count = len(blueprint.stages)
    return response


@router.delete("/{blueprint_id}", status_code=204)
async def delete_blueprint(
    blueprint_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    force: bool = False
):
    """Delete blueprint (draft only)"""
    blueprint = db.query(QABlueprint).filter(
        QABlueprint.id == blueprint_id
    ).first()
    
    if not blueprint:
        raise HTTPException(status_code=404, detail="Blueprint not found")
    
    require_company_access(blueprint.company_id, current_user)
    
    if current_user.role not in [UserRole.admin, UserRole.qa_manager]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Only draft blueprints can be deleted
    if blueprint.status != BlueprintStatus.draft:
        if not force or current_user.role != UserRole.admin:
            raise HTTPException(
                status_code=403,
                detail="Only draft blueprints can be deleted. Use force=true for admins to delete published blueprints."
            )
    
    # Create audit log
    audit_log = QABlueprintAuditLog(
        blueprint_id=blueprint.id,
        changed_by=current_user.id,
        change_type=ChangeType.delete,
        change_summary=f"Deleted blueprint '{blueprint.name}'"
    )
    db.add(audit_log)
    
    db.delete(blueprint)
    db.commit()
    
    return None


@router.post("/{blueprint_id}/duplicate", response_model=BlueprintResponse, status_code=201)
async def duplicate_blueprint(
    blueprint_id: str,
    duplicate_data: Optional[BlueprintDuplicateRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a copy of a blueprint"""
    original = db.query(QABlueprint).filter(
        QABlueprint.id == blueprint_id
    ).first()
    
    if not original:
        raise HTTPException(status_code=404, detail="Blueprint not found")
    
    require_company_access(original.company_id, current_user)
    
    # Create new blueprint
    new_name = duplicate_data.name if duplicate_data and duplicate_data.name else f"{original.name} (Copy)"
    
    # Check for duplicate name
    existing = db.query(QABlueprint).filter(
        QABlueprint.company_id == current_user.company_id,
        QABlueprint.name == new_name
    ).first()
    
    if existing:
        raise HTTPException(status_code=409, detail="Blueprint with this name already exists")
    
    new_blueprint = QABlueprint(
        company_id=current_user.company_id,
        name=new_name,
        description=original.description,
        status=BlueprintStatus.draft,
        version_number=1,
        created_by=current_user.id,
        updated_by=current_user.id,
        extra_metadata=original.extra_metadata.copy() if original.extra_metadata else None
    )
    db.add(new_blueprint)
    db.flush()
    
    # Copy stages and behaviors
    for stage in original.stages:
        new_stage = QABlueprintStage(
            blueprint_id=new_blueprint.id,
            stage_name=stage.stage_name,
            ordering_index=stage.ordering_index,
            stage_weight=stage.stage_weight,
            extra_metadata=stage.extra_metadata.copy() if stage.extra_metadata else None
        )
        db.add(new_stage)
        db.flush()
        
        for behavior in stage.behaviors:
            new_behavior = QABlueprintBehavior(
                stage_id=new_stage.id,
                behavior_name=behavior.behavior_name,
                description=behavior.description,
                behavior_type=behavior.behavior_type,
                detection_mode=behavior.detection_mode,
                phrases=behavior.phrases.copy() if behavior.phrases else None,
                weight=behavior.weight,
                critical_action=behavior.critical_action,
                ui_order=behavior.ui_order,
                extra_metadata=behavior.extra_metadata.copy() if behavior.extra_metadata else None
            )
            db.add(new_behavior)
    
    db.commit()
    db.refresh(new_blueprint)
    
    response = BlueprintResponse.model_validate(new_blueprint)
    response.stages_count = len(new_blueprint.stages)
    return response


# ==================== Stage Management ====================

@router.post("/{blueprint_id}/stages", response_model=StageResponse, status_code=201)
async def create_stage(
    blueprint_id: str,
    stage_data: StageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add stage to blueprint"""
    blueprint = db.query(QABlueprint).filter(
        QABlueprint.id == blueprint_id
    ).first()
    
    if not blueprint:
        raise HTTPException(status_code=404, detail="Blueprint not found")
    
    require_company_access(blueprint.company_id, current_user)
    
    if blueprint.status != BlueprintStatus.draft:
        raise HTTPException(status_code=403, detail="Only draft blueprints can be modified")
    
    # Check for duplicate ordering_index
    existing = db.query(QABlueprintStage).filter(
        QABlueprintStage.blueprint_id == blueprint_id,
        QABlueprintStage.ordering_index == stage_data.ordering_index
    ).first()
    
    if existing:
        raise HTTPException(status_code=409, detail="Stage with this ordering_index already exists")
    
    stage = QABlueprintStage(
        blueprint_id=blueprint_id,
        stage_name=stage_data.stage_name,
        ordering_index=stage_data.ordering_index,
        stage_weight=stage_data.stage_weight,
        extra_metadata=stage_data.metadata
    )
    
    db.add(stage)
    db.flush()  # Flush to get stage.id
    
    # Add behaviors if provided
    for behavior_data in stage_data.behaviors:
        behavior = QABlueprintBehavior(
            stage_id=stage.id,
            behavior_name=behavior_data.behavior_name,
            description=behavior_data.description,
            behavior_type=behavior_data.behavior_type,
            detection_mode=behavior_data.detection_mode,
            phrases=behavior_data.phrases,
            weight=behavior_data.weight,
            critical_action=behavior_data.critical_action,
            ui_order=behavior_data.ui_order or 0,
            extra_metadata=behavior_data.metadata
        )
        db.add(behavior)
    
    db.commit()
    db.refresh(stage)
    # Reload with behaviors for response
    stage = db.query(QABlueprintStage).options(
        joinedload(QABlueprintStage.behaviors)
    ).filter(QABlueprintStage.id == stage.id).first()
    
    return StageResponse.model_validate(stage)


@router.put("/{blueprint_id}/stages/{stage_id}", response_model=StageResponse)
async def update_stage(
    blueprint_id: str,
    stage_id: str,
    stage_data: StageUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update stage"""
    stage = db.query(QABlueprintStage).filter(
        QABlueprintStage.id == stage_id,
        QABlueprintStage.blueprint_id == blueprint_id
    ).first()
    
    if not stage:
        raise HTTPException(status_code=404, detail="Stage not found")
    
    require_company_access(stage.blueprint.company_id, current_user)
    
    if stage.blueprint.status != BlueprintStatus.draft:
        raise HTTPException(status_code=403, detail="Only draft blueprints can be modified")
    
    if stage_data.stage_name is not None:
        stage.stage_name = stage_data.stage_name
    if stage_data.ordering_index is not None:
        stage.ordering_index = stage_data.ordering_index
    if stage_data.stage_weight is not None:
        stage.stage_weight = stage_data.stage_weight
    if stage_data.metadata is not None:
        stage.extra_metadata = stage_data.metadata
    
    db.commit()
    db.refresh(stage)
    
    return StageResponse.model_validate(stage)


@router.delete("/{blueprint_id}/stages/{stage_id}", status_code=204)
async def delete_stage(
    blueprint_id: str,
    stage_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete stage"""
    stage = db.query(QABlueprintStage).filter(
        QABlueprintStage.id == stage_id,
        QABlueprintStage.blueprint_id == blueprint_id
    ).first()
    
    if not stage:
        raise HTTPException(status_code=404, detail="Stage not found")
    
    require_company_access(stage.blueprint.company_id, current_user)
    
    if stage.blueprint.status != BlueprintStatus.draft:
        raise HTTPException(status_code=403, detail="Only draft blueprints can be modified")
    
    db.delete(stage)
    db.commit()
    
    return None


# ==================== Behavior Management ====================

@router.post("/{blueprint_id}/stages/{stage_id}/behaviors", response_model=BehaviorResponse, status_code=201)
async def create_behavior(
    blueprint_id: str,
    stage_id: str,
    behavior_data: BehaviorCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add behavior to stage"""
    stage = db.query(QABlueprintStage).filter(
        QABlueprintStage.id == stage_id,
        QABlueprintStage.blueprint_id == blueprint_id
    ).first()
    
    if not stage:
        raise HTTPException(status_code=404, detail="Stage not found")
    
    require_company_access(stage.blueprint.company_id, current_user)
    
    if stage.blueprint.status != BlueprintStatus.draft:
        raise HTTPException(status_code=403, detail="Only draft blueprints can be modified")
    
    # Check for duplicate behavior name
    existing = db.query(QABlueprintBehavior).filter(
        QABlueprintBehavior.stage_id == stage_id,
        QABlueprintBehavior.behavior_name == behavior_data.behavior_name
    ).first()
    
    if existing:
        raise HTTPException(status_code=409, detail="Behavior with this name already exists in this stage")
    
    behavior = QABlueprintBehavior(
        stage_id=stage_id,
        behavior_name=behavior_data.behavior_name,
        description=behavior_data.description,
        behavior_type=behavior_data.behavior_type,
        detection_mode=behavior_data.detection_mode,
        phrases=behavior_data.phrases,
        weight=behavior_data.weight,
        critical_action=behavior_data.critical_action,
        ui_order=behavior_data.ui_order or 0,
        extra_metadata=behavior_data.metadata
    )
    
    db.add(behavior)
    db.commit()
    db.refresh(behavior)
    
    return BehaviorResponse.model_validate(behavior)


@router.put("/{blueprint_id}/stages/{stage_id}/behaviors/{behavior_id}", response_model=BehaviorResponse)
async def update_behavior(
    blueprint_id: str,
    stage_id: str,
    behavior_id: str,
    behavior_data: BehaviorUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update behavior"""
    behavior = db.query(QABlueprintBehavior).filter(
        QABlueprintBehavior.id == behavior_id,
        QABlueprintBehavior.stage_id == stage_id
    ).first()
    
    if not behavior:
        raise HTTPException(status_code=404, detail="Behavior not found")
    
    require_company_access(behavior.stage.blueprint.company_id, current_user)
    
    if behavior.stage.blueprint.status != BlueprintStatus.draft:
        raise HTTPException(status_code=403, detail="Only draft blueprints can be modified")
    
    if behavior_data.behavior_name is not None:
        behavior.behavior_name = behavior_data.behavior_name
    if behavior_data.description is not None:
        behavior.description = behavior_data.description
    if behavior_data.behavior_type is not None:
        behavior.behavior_type = behavior_data.behavior_type
    if behavior_data.detection_mode is not None:
        behavior.detection_mode = behavior_data.detection_mode
    if behavior_data.phrases is not None:
        behavior.phrases = behavior_data.phrases
    if behavior_data.weight is not None:
        behavior.weight = behavior_data.weight
    if behavior_data.critical_action is not None:
        behavior.critical_action = behavior_data.critical_action
    if behavior_data.ui_order is not None:
        behavior.ui_order = behavior_data.ui_order
    if behavior_data.metadata is not None:
        behavior.extra_metadata = behavior_data.metadata
    
    db.commit()
    db.refresh(behavior)
    
    return BehaviorResponse.model_validate(behavior)


@router.delete("/{blueprint_id}/stages/{stage_id}/behaviors/{behavior_id}", status_code=204)
async def delete_behavior(
    blueprint_id: str,
    stage_id: str,
    behavior_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete behavior"""
    behavior = db.query(QABlueprintBehavior).filter(
        QABlueprintBehavior.id == behavior_id,
        QABlueprintBehavior.stage_id == stage_id
    ).first()
    
    if not behavior:
        raise HTTPException(status_code=404, detail="Behavior not found")
    
    require_company_access(behavior.stage.blueprint.company_id, current_user)
    
    if behavior.stage.blueprint.status != BlueprintStatus.draft:
        raise HTTPException(status_code=403, detail="Only draft blueprints can be modified")
    
    db.delete(behavior)
    db.commit()
    
    return None


# ==================== Version Management ====================

@router.get("/{blueprint_id}/versions", response_model=List[BlueprintVersionResponse])
async def list_versions(
    blueprint_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List published versions of a blueprint"""
    blueprint = db.query(QABlueprint).filter(
        QABlueprint.id == blueprint_id
    ).first()
    
    if not blueprint:
        raise HTTPException(status_code=404, detail="Blueprint not found")
    
    require_company_access(blueprint.company_id, current_user)
    
    versions = db.query(QABlueprintVersion).filter(
        QABlueprintVersion.blueprint_id == blueprint_id
    ).order_by(QABlueprintVersion.version_number.desc()).all()
    
    return [BlueprintVersionResponse.model_validate(v) for v in versions]


@router.get("/{blueprint_id}/versions/{version_number}", response_model=BlueprintVersionResponse)
async def get_version(
    blueprint_id: str,
    version_number: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific published version snapshot"""
    version = db.query(QABlueprintVersion).filter(
        QABlueprintVersion.blueprint_id == blueprint_id,
        QABlueprintVersion.version_number == version_number
    ).first()
    
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    require_company_access(version.blueprint.company_id, current_user)
    
    return BlueprintVersionResponse.model_validate(version)


# ==================== Publish & Compiler ====================

@router.post("/{blueprint_id}/publish", response_model=PublishResponse, status_code=202)
async def publish_blueprint(
    blueprint_id: str,
    publish_data: Optional[PublishRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    """Validate and compile blueprint (triggers background job)"""
    # Eager load stages and behaviors to avoid lazy loading issues
    blueprint = db.query(QABlueprint).options(
        joinedload(QABlueprint.stages).joinedload(QABlueprintStage.behaviors)
    ).filter(
        QABlueprint.id == blueprint_id
    ).first()
    
    if not blueprint:
        raise HTTPException(status_code=404, detail="Blueprint not found")
    
    require_company_access(blueprint.company_id, current_user)
    
    if current_user.role not in [UserRole.admin, UserRole.qa_manager]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Validate blueprint
    force_normalize = publish_data.force_normalize_weights if publish_data else False
    is_valid, errors, warnings = validator.validate_for_publish(blueprint, db, force_normalize)
    
    if not is_valid:
        error_details = [e.to_dict() for e in errors]
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "PUBLISH_VALIDATION_FAILED",
                "message": "Blueprint failed validation",
                "errors": error_details,
                "warnings": warnings
            }
        )
    
    # Normalize weights if requested
    if force_normalize:
        validator.normalize_weights(blueprint, True, True)
        db.commit()
    
    # Create blueprint version snapshot
    snapshot = {
        "name": blueprint.name,
        "description": blueprint.description,
        "metadata": blueprint.extra_metadata,
        "stages": []
    }
    
    for stage in blueprint.stages:
        stage_data = {
            "id": stage.id,
            "stage_name": stage.stage_name,
            "ordering_index": stage.ordering_index,
            "stage_weight": float(stage.stage_weight) if stage.stage_weight else None,
            "metadata": stage.extra_metadata,
            "behaviors": []
        }
        
        for behavior in stage.behaviors:
            behavior_data = {
                "id": behavior.id,
                "behavior_name": behavior.behavior_name,
                "description": behavior.description,
                "behavior_type": behavior.behavior_type.value,
                "detection_mode": behavior.detection_mode.value,
                "phrases": behavior.phrases,
                "weight": float(behavior.weight),
                "critical_action": behavior.critical_action.value if behavior.critical_action else None,
                "ui_order": behavior.ui_order,
                "metadata": behavior.extra_metadata
            }
            stage_data["behaviors"].append(behavior_data)
        
        snapshot["stages"].append(stage_data)
    
    # Increment version number
    new_version_number = blueprint.version_number + 1
    
    blueprint_version = QABlueprintVersion(
        blueprint_id=blueprint_id,
        version_number=new_version_number,
        snapshot=snapshot,
        published_by=current_user.id
    )
    db.add(blueprint_version)
    db.flush()
    
    # Enqueue compile job (or generate local job_id if Cloud Tasks not available)
    compile_options = publish_data.compiler_options if publish_data else {}
    job_id = None
    try:
        job_id = cloud_tasks_service.enqueue_compile_job(
            blueprint_id=blueprint_id,
            blueprint_version_id=blueprint_version.id,
            compile_options=compile_options,
            user_id=current_user.id
        )
    except Exception as e:
        logger.warning(f"Failed to enqueue compile job (Cloud Tasks may not be configured): {e}")
        job_id = None
    
    # If Cloud Tasks is not configured, run compile job in background using FastAPI BackgroundTasks
    if not job_id:
        logger.warning("Cloud Tasks not available. Running compile job in background...")
        job_id = f"local-{blueprint_version.id}"
        
        # Schedule compile job to run in background after response is sent
        from app.tasks.compile_blueprint_job import compile_blueprint_job_handler
        
        async def run_compile_job():
            """Run compile job"""
            try:
                payload = {
                    "blueprint_id": blueprint_id,
                    "blueprint_version_id": blueprint_version.id,
                    "compile_options": compile_options,
                    "user_id": current_user.id
                }
                result = await compile_blueprint_job_handler(payload)
                logger.info(f"Background compile job completed: {result.get('status', 'unknown')}")
            except Exception as e:
                logger.error(f"Background compile job failed: {e}", exc_info=True)
        
        # Add background task (will run after response is sent)
        background_tasks.add_task(run_compile_job)
    
    # Create audit log
    audit_log = QABlueprintAuditLog(
        blueprint_id=blueprint_id,
        changed_by=current_user.id,
        change_type=ChangeType.publish,
        change_summary=f"Published blueprint version {new_version_number}"
    )
    db.add(audit_log)
    
    # Update blueprint status to published
    blueprint.status = BlueprintStatus.published
    blueprint.version_number = new_version_number
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to commit blueprint publish: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to publish blueprint: {str(e)}")
    
    return PublishResponse(
        job_id=job_id,
        blueprint_id=blueprint_id,
        status="queued" if not job_id.startswith("local-") else "compiling",
        links={
            "job_status": f"/api/blueprints/{blueprint_id}/publish_status/{job_id}"
        }
    )


@router.get("/{blueprint_id}/publish_status/{job_id}", response_model=PublishStatusResponse)
async def get_publish_status(
    blueprint_id: str,
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get publish/compile job status"""
    blueprint = db.query(QABlueprint).filter(
        QABlueprint.id == blueprint_id
    ).first()
    
    if not blueprint:
        raise HTTPException(status_code=404, detail="Blueprint not found")
    
    require_company_access(blueprint.company_id, current_user)
    
    # Extract blueprint_version_id from job_id (format: local-{version_id} or Cloud Tasks ID)
    if job_id.startswith("local-"):
        blueprint_version_id = job_id.replace("local-", "")
    else:
        # For Cloud Tasks, we'd need to extract version_id differently
        # For now, check the latest version
        latest_version = db.query(QABlueprintVersion).filter(
            QABlueprintVersion.blueprint_id == blueprint_id
        ).order_by(QABlueprintVersion.version_number.desc()).first()
        blueprint_version_id = latest_version.id if latest_version else None
    
    if not blueprint_version_id:
        return PublishStatusResponse(
            job_id=job_id,
            status="failed",
            progress=0,
            errors=[{"message": "Could not find blueprint version"}]
        )
    
    # Check compilation status by looking at blueprint version and compiler map
    blueprint_version = db.query(QABlueprintVersion).filter(
        QABlueprintVersion.id == blueprint_version_id
    ).first()
    
    if not blueprint_version:
        return PublishStatusResponse(
            job_id=job_id,
            status="failed",
            progress=0,
            errors=[{"message": "Blueprint version not found"}]
        )
    
    # Check if compilation completed
    compiler_map = db.query(QABlueprintCompilerMap).filter(
        QABlueprintCompilerMap.blueprint_version_id == blueprint_version_id
    ).first()
    
    if blueprint_version.compiled_flow_version_id or (compiler_map and compiler_map.flow_version_id):
        # Compilation succeeded
        return PublishStatusResponse(
            job_id=job_id,
            status="succeeded",
            progress=100,
            compiled_flow_version_id=blueprint_version.compiled_flow_version_id or (compiler_map.flow_version_id if compiler_map else None)
        )
    else:
        # Still compiling (or not started yet)
        # If no compiler_map exists, compilation might not have started
        # Try to trigger it manually if it's been more than a few seconds
        if not compiler_map:
            logger.warning(f"No compiler_map found for blueprint version {blueprint_version_id}. Compilation may not have started.")
            # Could trigger compilation here, but for now just return running status
        
        return PublishStatusResponse(
            job_id=job_id,
            status="running",
            progress=50
        )


@router.post("/{blueprint_id}/compile", status_code=202)
async def compile_blueprint_manual(
    blueprint_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Manually trigger compilation of the latest blueprint version"""
    blueprint = db.query(QABlueprint).filter(
        QABlueprint.id == blueprint_id
    ).first()
    
    if not blueprint:
        raise HTTPException(status_code=404, detail="Blueprint not found")
    
    require_company_access(blueprint.company_id, current_user)
    
    # Get latest version
    from app.models.qa_blueprint_version import QABlueprintVersion
    latest_version = db.query(QABlueprintVersion).filter(
        QABlueprintVersion.blueprint_id == blueprint_id
    ).order_by(QABlueprintVersion.version_number.desc()).first()
    
    if not latest_version:
        raise HTTPException(status_code=400, detail="No published version found. Please publish the blueprint first.")
    
    # Check if already compiled
    from app.models.qa_blueprint_compiler_map import QABlueprintCompilerMap
    compiler_map = db.query(QABlueprintCompilerMap).filter(
        QABlueprintCompilerMap.blueprint_version_id == latest_version.id
    ).first()
    
    if compiler_map and compiler_map.flow_version_id:
        return {
            "status": "already_compiled",
            "message": "Blueprint version is already compiled",
            "compiled_flow_version_id": compiler_map.flow_version_id
        }
    
    # Trigger compilation
    from app.tasks.compile_blueprint_job import compile_blueprint_job_handler
    
    async def run_compile_job():
        """Run compile job"""
        try:
            payload = {
                "blueprint_id": blueprint_id,
                "blueprint_version_id": latest_version.id,
                "compile_options": {},
                "user_id": current_user.id
            }
            result = await compile_blueprint_job_handler(payload)
            logger.info(f"Manual compile job completed: {result.get('status', 'unknown')}")
        except Exception as e:
            logger.error(f"Manual compile job failed: {e}", exc_info=True)
    
    background_tasks.add_task(run_compile_job)
    
    return {
        "status": "started",
        "message": "Compilation job started",
        "blueprint_version_id": latest_version.id
    }


# ==================== Templates & Import/Export ====================

@router.get("/templates", response_model=List[Dict[str, Any]])
async def list_templates(
    current_user: User = Depends(get_current_user)
):
    """List preset templates"""
    # TODO: Load from templates directory or database
    templates = [
        {
            "id": "standard_support",
            "name": "Standard Support",
            "description": "Template for general customer support",
            "preview_stages": ["Opening", "Verification", "Resolution", "Closing"],
            "recommended_for": ["support", "customer_service"]
        },
        {
            "id": "billing_support",
            "name": "Billing Support",
            "description": "Template for billing and payment inquiries",
            "preview_stages": ["Opening", "Verification", "Billing Inquiry", "Resolution", "Closing"],
            "recommended_for": ["billing", "payments"]
        }
    ]
    return templates


@router.post("/import", response_model=BlueprintResponse, status_code=201)
async def import_blueprint(
    import_data: BlueprintImportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Import template JSON"""
    # TODO: Implement import logic
    # For now, create blueprint from JSON
    blueprint_json = import_data.blueprint_json
    
    blueprint = QABlueprint(
        company_id=current_user.company_id,
        name=import_data.name or blueprint_json.get("name", "Imported Blueprint"),
        description=blueprint_json.get("description"),
        status=BlueprintStatus.draft,
        version_number=1,
        created_by=current_user.id,
        updated_by=current_user.id,
        metadata=blueprint_json.get("metadata")
    )
    db.add(blueprint)
    db.flush()
    
    # Import stages and behaviors from JSON
    for stage_data in blueprint_json.get("stages", []):
        stage = QABlueprintStage(
            blueprint_id=blueprint.id,
            stage_name=stage_data["stage_name"],
            ordering_index=stage_data["ordering_index"],
            stage_weight=stage_data.get("stage_weight"),
            metadata=stage_data.get("metadata")
        )
        db.add(stage)
        db.flush()
        
        for behavior_data in stage_data.get("behaviors", []):
            behavior = QABlueprintBehavior(
                stage_id=stage.id,
                behavior_name=behavior_data["behavior_name"],
                description=behavior_data.get("description"),
                behavior_type=behavior_data.get("behavior_type", "required"),
                detection_mode=behavior_data.get("detection_mode", "semantic"),
                phrases=behavior_data.get("phrases"),
                weight=behavior_data.get("weight", 0),
                critical_action=behavior_data.get("critical_action"),
                ui_order=behavior_data.get("ui_order", 0),
                metadata=behavior_data.get("metadata")
            )
            db.add(behavior)
    
    db.commit()
    db.refresh(blueprint)
    
    response = BlueprintResponse.model_validate(blueprint)
    response.stages_count = len(blueprint.stages)
    return response


@router.post("/{blueprint_id}/export", response_model=BlueprintExportResponse)
async def export_blueprint(
    blueprint_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export blueprint JSON"""
    blueprint = db.query(QABlueprint).filter(
        QABlueprint.id == blueprint_id
    ).first()
    
    if not blueprint:
        raise HTTPException(status_code=404, detail="Blueprint not found")
    
    require_company_access(blueprint.company_id, current_user)
    
    # Build export JSON
    export_data = {
        "name": blueprint.name,
        "description": blueprint.description,
        "metadata": blueprint.extra_metadata,
        "stages": []
    }
    
    for stage in blueprint.stages:
        stage_data = {
            "stage_name": stage.stage_name,
            "ordering_index": stage.ordering_index,
            "stage_weight": float(stage.stage_weight) if stage.stage_weight else None,
            "metadata": stage.extra_metadata,
            "behaviors": []
        }
        
        for behavior in stage.behaviors:
            behavior_data = {
                "behavior_name": behavior.behavior_name,
                "description": behavior.description,
                "behavior_type": behavior.behavior_type.value,
                "detection_mode": behavior.detection_mode.value,
                "phrases": behavior.phrases,
                "weight": float(behavior.weight),
                "critical_action": behavior.critical_action.value if behavior.critical_action else None,
                "metadata": behavior.extra_metadata
            }
            stage_data["behaviors"].append(behavior_data)
        
        export_data["stages"].append(stage_data)
    
    return BlueprintExportResponse(
        blueprint=export_data,
        exported_at=datetime.utcnow()
    )

