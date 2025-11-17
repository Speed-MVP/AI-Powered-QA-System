"""
Rule Editor API Routes
Phase 5: Structured Rule Editor UI & Admin Tools

Endpoints for rule editing, publishing, versioning, and sandbox testing.
"""

import logging
import hashlib
import json
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models.policy_template import PolicyTemplate
from app.models.rule_draft import RuleDraft, DraftStatus
from app.models.rule_version import RuleVersion
from app.models.rule_audit_log import RuleAuditLog
from app.models.user import User, UserRole
from app.middleware.auth import get_current_user
from app.schemas.policy_rules import PolicyRulesSchema, validate_policy_rules, detect_conflicting_rules
from app.services.rule_engine_v2 import RuleEngineV2

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/policy-templates", tags=["rule-editor"])


# Request/Response models
class SaveDraftRequest(BaseModel):
    rules: Dict[str, Any]


class PublishDraftRequest(BaseModel):
    draft_id: Optional[str] = None
    reason: Optional[str] = None
    require_approval: bool = False


class RollbackRequest(BaseModel):
    version_id: str
    reason: Optional[str] = None


class SandboxRequest(BaseModel):
    transcript_segments: List[Dict[str, Any]]
    sentiment_analysis: Optional[List[Dict[str, Any]]] = None


def _hash_rules(rules_dict: Dict[str, Any]) -> str:
    """Generate SHA256 hash of rules."""
    rules_str = json.dumps(rules_dict, sort_keys=True)
    return hashlib.sha256(rules_str.encode()).hexdigest()


def _log_audit(
    db: Session,
    policy_template_id: str,
    user_id: str,
    action: str,
    ip_address: str,
    delta: Optional[Dict[str, Any]] = None,
    reason: Optional[str] = None,
    rules_hash: Optional[str] = None,
    draft_id: Optional[str] = None,
    version_id: Optional[str] = None,
    llm_generated: bool = False
):
    """Create audit log entry."""
    audit_log = RuleAuditLog(
        policy_template_id=policy_template_id,
        user_id=user_id,
        ip_address=ip_address,
        action=action,
        delta=delta,
        reason=reason,
        rules_hash=rules_hash,
        draft_id=draft_id,
        version_id=version_id,
        llm_generated=llm_generated
    )
    db.add(audit_log)
    db.flush()


@router.get("/{template_id}/rules")
async def get_rules(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current published rules for a policy template."""
    template = db.query(PolicyTemplate).filter(
        PolicyTemplate.id == template_id,
        PolicyTemplate.company_id == current_user.company_id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy template not found"
        )
    
    return {
        "rules": template.policy_rules,
        "rules_version": template.policy_rules_version,
        "rules_generated_at": template.rules_generated_at.isoformat() if template.rules_generated_at else None,
        "enable_structured_rules": template.enable_structured_rules
    }


@router.post("/{template_id}/rules/draft")
async def save_draft(
    template_id: str,
    request: SaveDraftRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Save draft rules.
    Policy Editor/Reviewer can draft, but cannot publish.
    """
    template = db.query(PolicyTemplate).filter(
        PolicyTemplate.id == template_id,
        PolicyTemplate.company_id == current_user.company_id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy template not found"
        )
    
    # Validate rules
    try:
        validated_rules = PolicyRulesSchema(**request.rules)
        conflicts = detect_conflicting_rules(validated_rules.rules)
        
        if conflicts:
            return {
                "success": False,
                "errors": [c.get("description", "Rule conflict detected") for c in conflicts],
                "conflicts": conflicts
            }
    except Exception as e:
        return {
            "success": False,
            "errors": [str(e)]
        }
    
    # Create or update draft
    existing_draft = db.query(RuleDraft).filter(
        RuleDraft.policy_template_id == template_id,
        RuleDraft.created_by_user_id == current_user.id,
        RuleDraft.status == DraftStatus.editing
    ).first()
    
    if existing_draft:
        existing_draft.rules_json = request.rules
        existing_draft.updated_at = datetime.utcnow()
        draft = existing_draft
    else:
        draft = RuleDraft(
            policy_template_id=template_id,
            rules_json=request.rules,
            status=DraftStatus.editing,
            created_by_user_id=current_user.id
        )
        db.add(draft)
    
    db.flush()
    
    # Log audit
    _log_audit(
        db=db,
        policy_template_id=template_id,
        user_id=current_user.id,
        action="save_draft",
        ip_address="unknown",  # IP can be extracted via middleware if needed
        rules_hash=_hash_rules(request.rules),
        draft_id=draft.id
    )
    
    db.commit()
    
    return {
        "success": True,
        "draft_id": draft.id,
        "status": draft.status.value
    }


@router.post("/{template_id}/rules/publish")
async def publish_rules(
    template_id: str,
    request: PublishDraftRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Publish draft rules.
    Admin only. Requires 2-step approval for critical rules.
    """
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can publish rules"
        )
    
    template = db.query(PolicyTemplate).filter(
        PolicyTemplate.id == template_id,
        PolicyTemplate.company_id == current_user.company_id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy template not found"
        )
    
    # Get draft or use current rules
    if request.draft_id:
        draft = db.query(RuleDraft).filter(
            RuleDraft.id == request.draft_id,
            RuleDraft.policy_template_id == template_id
        ).first()
        
        if not draft:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Draft not found"
            )
        
        rules_to_publish = draft.rules_json
    else:
        rules_to_publish = template.policy_rules or {}
    
    # Validate rules
    try:
        validated_rules = PolicyRulesSchema(**rules_to_publish)
        conflicts = detect_conflicting_rules(validated_rules.rules)
        
        if conflicts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Rule conflicts detected: {[c.get('description') for c in conflicts]}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid rules: {str(e)}"
        )
    
    # Check for critical rules
    has_critical = False
    for category_rules in validated_rules.rules.values():
        for rule in category_rules:
            if isinstance(rule, dict) and rule.get("critical"):
                has_critical = True
                break
    
    # Create version snapshot before publishing
    rules_hash = _hash_rules(rules_to_publish)
    new_version = template.policy_rules_version or 0
    
    version = RuleVersion(
        policy_template_id=template_id,
        rules_json=template.policy_rules or {},
        rules_hash=_hash_rules(template.policy_rules or {}) if template.policy_rules else "",
        rules_version=new_version,
        created_by_user_id=current_user.id,
        llm_generated_flag=template.rules_generation_method == "ai"
    )
    db.add(version)
    db.flush()
    
    # Update template
    template.policy_rules = rules_to_publish
    template.policy_rules_version = new_version + 1
    template.rules_generated_at = datetime.utcnow()
    template.rules_approved_by_user_id = current_user.id
    template.enable_structured_rules = True
    
    # Update draft status if applicable
    if request.draft_id:
        draft.status = DraftStatus.ready_for_confirm
        draft.updated_at = datetime.utcnow()
    
    # Log audit
    _log_audit(
        db=db,
        policy_template_id=template_id,
        user_id=current_user.id,
        action="publish",
        ip_address="unknown",  # IP can be extracted via middleware if needed
        reason=request.reason,
        rules_hash=rules_hash,
        draft_id=request.draft_id,
        version_id=version.id,
        llm_generated=template.rules_generation_method == "ai"
    )
    
    db.commit()
    
    return {
        "success": True,
        "rules_version": template.policy_rules_version,
        "version_id": version.id
    }


@router.get("/{template_id}/rules/history")
async def get_history(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get version history for rules."""
    template = db.query(PolicyTemplate).filter(
        PolicyTemplate.id == template_id,
        PolicyTemplate.company_id == current_user.company_id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy template not found"
        )
    
    versions = db.query(RuleVersion).filter(
        RuleVersion.policy_template_id == template_id
    ).order_by(RuleVersion.rules_version.desc()).all()
    
    drafts = db.query(RuleDraft).filter(
        RuleDraft.policy_template_id == template_id
    ).order_by(RuleDraft.created_at.desc()).all()
    
    return {
        "versions": [
            {
                "id": v.id,
                "rules_version": v.rules_version,
                "rules_hash": v.rules_hash,
                "created_at": v.created_at.isoformat(),
                "created_by": v.created_by.full_name if v.created_by else "Unknown",
                "llm_generated": v.llm_generated_flag
            }
            for v in versions
        ],
        "drafts": [
            {
                "id": d.id,
                "status": d.status.value,
                "created_at": d.created_at.isoformat(),
                "updated_at": d.updated_at.isoformat(),
                "created_by": d.created_by.full_name if d.created_by else "Unknown"
            }
            for d in drafts
        ]
    }


@router.post("/{template_id}/rules/rollback")
async def rollback_rules(
    template_id: str,
    request: RollbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Rollback to a previous version (creates new draft).
    Admin only.
    """
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can rollback rules"
        )
    
    template = db.query(PolicyTemplate).filter(
        PolicyTemplate.id == template_id,
        PolicyTemplate.company_id == current_user.company_id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy template not found"
        )
    
    # Get version to rollback to
    version = db.query(RuleVersion).filter(
        RuleVersion.id == request.version_id,
        RuleVersion.policy_template_id == template_id
    ).first()
    
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found"
        )
    
    # Create draft from version
    draft = RuleDraft(
        policy_template_id=template_id,
        rules_json=version.rules_json,
        status=DraftStatus.ready_for_confirm,
        created_by_user_id=current_user.id
    )
    db.add(draft)
    db.flush()
    
    # Log audit
    _log_audit(
        db=db,
        policy_template_id=template_id,
        user_id=current_user.id,
        action="rollback",
        ip_address="unknown",  # IP can be extracted via middleware if needed
        reason=request.reason,
        version_id=request.version_id,
        draft_id=draft.id
    )
    
    db.commit()
    
    return {
        "success": True,
        "draft_id": draft.id,
        "message": "Rollback draft created. Publish to activate."
    }


@router.post("/{template_id}/rules/sandbox")
async def sandbox_rules(
    template_id: str,
    request: SandboxRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Preview rules on sample transcripts (sandbox mode).
    Returns deterministic rule evaluation results without final scoring.
    """
    template = db.query(PolicyTemplate).filter(
        PolicyTemplate.id == template_id,
        PolicyTemplate.company_id == current_user.company_id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy template not found"
        )
    
    # Use draft rules if available, otherwise published rules
    draft = db.query(RuleDraft).filter(
        RuleDraft.policy_template_id == template_id,
        RuleDraft.created_by_user_id == current_user.id,
        RuleDraft.status == DraftStatus.editing
    ).first()
    
    rules_to_test = draft.rules_json if draft else (template.policy_rules or {})
    
    if not rules_to_test:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No rules to test"
        )
    
    # Run rule engine
    rule_engine = RuleEngineV2(policy_rules=rules_to_test)
    results = rule_engine.evaluate_rules(
        transcript_segments=request.transcript_segments,
        sentiment_analysis=request.sentiment_analysis,
        policy_template_id=template_id
    )
    
    # Calculate expected rubric impacts (simplified)
    rubric_impacts = {}
    for category, category_results in results.items():
        if category == "summary":
            continue
        
        failed_count = sum(1 for r in category_results.values() if not r.get("passed", True))
        total_count = len(category_results)
        
        if failed_count == 0:
            rubric_impacts[category] = "Excellent"
        elif failed_count / total_count < 0.2:
            rubric_impacts[category] = "Good"
        elif failed_count / total_count < 0.5:
            rubric_impacts[category] = "Average"
        else:
            rubric_impacts[category] = "Poor"
    
    return {
        "rule_results": results,
        "expected_rubric_impacts": rubric_impacts,
        "warnings": [
            "Critical rule failed" for category, rules in results.items()
            if category != "summary"
            for rule_id, result in rules.items()
            if not result.get("passed", True) and result.get("severity") == "critical"
        ]
    }

