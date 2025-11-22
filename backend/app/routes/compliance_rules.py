"""
Phase 2: ComplianceRule API Routes
CRUD operations for ComplianceRules.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, UserRole
from app.models.compliance_rule import ComplianceRule, RuleType, Severity
from app.models.flow_version import FlowVersion
from app.middleware.auth import get_current_user
from app.middleware.permissions import require_company_access
from app.schemas.compliance_rule import (
    ComplianceRuleCreate,
    ComplianceRuleUpdate,
    ComplianceRuleResponse,
    RulePreviewResponse,
    generate_rule_preview,
)
from app.services.compliance_rule_validator import ComplianceRuleValidator
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/compliance-rules", tags=["compliance-rules"])


@router.get("", response_model=List[ComplianceRuleResponse])
async def list_compliance_rules(
    flow_version_id: Optional[str] = Query(None, description="Filter by FlowVersion ID"),
    active_only: bool = Query(False, description="Show only active rules"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List ComplianceRules, optionally filtered by FlowVersion"""
    query = db.query(ComplianceRule).join(FlowVersion).filter(
        FlowVersion.company_id == current_user.company_id
    )
    
    if flow_version_id:
        query = query.filter(ComplianceRule.flow_version_id == flow_version_id)
    
    if active_only:
        query = query.filter(ComplianceRule.active == True)
    
    rules = query.order_by(ComplianceRule.created_at.desc()).all()
    
    return rules


@router.post("", response_model=ComplianceRuleResponse)
async def create_compliance_rule(
    rule_data: ComplianceRuleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new ComplianceRule (admin or qa_manager only)"""
    if current_user.role not in [UserRole.admin, UserRole.qa_manager]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Get FlowVersion and verify access
    flow_version = db.query(FlowVersion).filter(
        FlowVersion.id == rule_data.flow_version_id
    ).first()
    
    if not flow_version:
        raise HTTPException(status_code=404, detail="FlowVersion not found")
    
    require_company_access(flow_version.company_id, current_user)
    
    # Validate rule params
    is_valid, errors = ComplianceRuleValidator.validate_rule_params(
        rule_data.rule_type,
        rule_data.params,
        flow_version
    )
    
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Invalid rule params: {', '.join(errors)}")
    
    # Validate applies_to_stages
    if rule_data.applies_to_stages:
        is_valid, errors = ComplianceRuleValidator.validate_applies_to_stages(
            rule_data.applies_to_stages,
            flow_version
        )
        
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid stage IDs: {', '.join(errors)}")
    
    # Check for forbidden/required phrase conflicts
    existing_rules = db.query(ComplianceRule).filter(
        ComplianceRule.flow_version_id == rule_data.flow_version_id,
        ComplianceRule.active == True
    ).all()
    
    # Create temporary rule object for conflict check
    temp_rule = ComplianceRule(
        id="temp",
        flow_version_id=rule_data.flow_version_id,
        rule_type=rule_data.rule_type,
        applies_to_stages=rule_data.applies_to_stages or [],
        params=rule_data.params
    )
    
    has_conflict, conflict_msg = ComplianceRuleValidator.check_forbidden_required_conflict(
        temp_rule,
        existing_rules,
        flow_version
    )
    
    if has_conflict:
        raise HTTPException(status_code=400, detail=conflict_msg)
    
    # Create rule
    rule = ComplianceRule(
        flow_version_id=rule_data.flow_version_id,
        title=rule_data.title,
        description=rule_data.description,
        severity=rule_data.severity,
        rule_type=rule_data.rule_type,
        applies_to_stages=rule_data.applies_to_stages or [],
        params=rule_data.params,
        active=rule_data.active
    )
    
    db.add(rule)
    db.commit()
    db.refresh(rule)
    
    return rule


@router.get("/{rule_id}", response_model=ComplianceRuleResponse)
async def get_compliance_rule(
    rule_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get ComplianceRule by ID"""
    rule = db.query(ComplianceRule).filter(ComplianceRule.id == rule_id).first()
    
    if not rule:
        raise HTTPException(status_code=404, detail="ComplianceRule not found")
    
    flow_version = db.query(FlowVersion).filter(FlowVersion.id == rule.flow_version_id).first()
    require_company_access(flow_version.company_id, current_user)
    
    return rule


@router.put("/{rule_id}", response_model=ComplianceRuleResponse)
async def update_compliance_rule(
    rule_id: str,
    rule_data: ComplianceRuleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update ComplianceRule (admin or qa_manager only)"""
    if current_user.role not in [UserRole.admin, UserRole.qa_manager]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    rule = db.query(ComplianceRule).filter(ComplianceRule.id == rule_id).first()
    
    if not rule:
        raise HTTPException(status_code=404, detail="ComplianceRule not found")
    
    flow_version = db.query(FlowVersion).filter(FlowVersion.id == rule.flow_version_id).first()
    require_company_access(flow_version.company_id, current_user)
    
    # If rule_type or params are being updated, validate
    rule_type = rule_data.rule_type if rule_data.rule_type is not None else rule.rule_type
    params = rule_data.params if rule_data.params is not None else rule.params
    
    if rule_data.rule_type is not None or rule_data.params is not None:
        is_valid, errors = ComplianceRuleValidator.validate_rule_params(
            rule_type,
            params,
            flow_version
        )
        
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid rule params: {', '.join(errors)}")
    
    # Validate applies_to_stages if being updated
    applies_to_stages = rule_data.applies_to_stages if rule_data.applies_to_stages is not None else rule.applies_to_stages
    
    if rule_data.applies_to_stages is not None:
        is_valid, errors = ComplianceRuleValidator.validate_applies_to_stages(
            applies_to_stages or [],
            flow_version
        )
        
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid stage IDs: {', '.join(errors)}")
    
    # Update fields
    if rule_data.title is not None:
        rule.title = rule_data.title
    if rule_data.description is not None:
        rule.description = rule_data.description
    if rule_data.severity is not None:
        rule.severity = rule_data.severity
    if rule_data.rule_type is not None:
        rule.rule_type = rule_data.rule_type
    if rule_data.applies_to_stages is not None:
        rule.applies_to_stages = rule_data.applies_to_stages
    if rule_data.params is not None:
        rule.params = rule_data.params
    if rule_data.active is not None:
        rule.active = rule_data.active
    
    db.commit()
    db.refresh(rule)
    
    return rule


@router.delete("/{rule_id}")
async def delete_compliance_rule(
    rule_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete ComplianceRule (admin or qa_manager only)"""
    if current_user.role not in [UserRole.admin, UserRole.qa_manager]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    rule = db.query(ComplianceRule).filter(ComplianceRule.id == rule_id).first()
    
    if not rule:
        raise HTTPException(status_code=404, detail="ComplianceRule not found")
    
    flow_version = db.query(FlowVersion).filter(FlowVersion.id == rule.flow_version_id).first()
    require_company_access(flow_version.company_id, current_user)
    
    db.delete(rule)
    db.commit()
    
    return {"message": "ComplianceRule deleted successfully"}


@router.post("/{rule_id}/toggle")
async def toggle_compliance_rule(
    rule_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Toggle ComplianceRule active status (admin or qa_manager only)"""
    if current_user.role not in [UserRole.admin, UserRole.qa_manager]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    rule = db.query(ComplianceRule).filter(ComplianceRule.id == rule_id).first()
    
    if not rule:
        raise HTTPException(status_code=404, detail="ComplianceRule not found")
    
    flow_version = db.query(FlowVersion).filter(FlowVersion.id == rule.flow_version_id).first()
    require_company_access(flow_version.company_id, current_user)
    
    rule.active = not rule.active
    db.commit()
    db.refresh(rule)
    
    return {"active": rule.active}


@router.get("/{rule_id}/preview", response_model=RulePreviewResponse)
async def get_rule_preview(
    rule_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get human-readable preview sentence for a rule"""
    rule = db.query(ComplianceRule).filter(ComplianceRule.id == rule_id).first()
    
    if not rule:
        raise HTTPException(status_code=404, detail="ComplianceRule not found")
    
    flow_version = db.query(FlowVersion).filter(FlowVersion.id == rule.flow_version_id).first()
    require_company_access(flow_version.company_id, current_user)
    
    rule_response = ComplianceRuleResponse.from_orm(rule)
    preview = generate_rule_preview(rule_response)
    
    return RulePreviewResponse(preview=preview)

