"""
Template Management API Routes
Includes standard template loading functionality.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, UserRole
from app.models.flow_version import FlowVersion
from app.models.flow_stage import FlowStage
from app.models.flow_step import FlowStep
from app.models.compliance_rule import ComplianceRule, RuleType, Severity
from app.models.rubric_template import RubricTemplate, RubricCategory, RubricMapping
from app.middleware.auth import get_current_user
from app.schemas.flow_version import FlowVersionResponse
from app.schemas.compliance_rule import ComplianceRuleResponse
from app.schemas.rubric_template import RubricTemplateResponse
from typing import Dict, Any, List
import json
import os
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/templates", tags=["templates"])


def get_template_path() -> str:
    """Get the path to the standard template JSON file"""
    # Get the backend directory (parent of app)
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    template_path = os.path.join(backend_dir, "data", "templates", "standard_bpo_template.json")
    return template_path


@router.post("/load-standard", response_model=Dict[str, Any])
async def load_standard_template(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Load the standard BPO template (SOP + Compliance Rules + Rubric).
    Creates a complete template bundle for the user's company.
    """
    if current_user.role not in [UserRole.admin, UserRole.qa_manager]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Load template JSON
    template_path = get_template_path()
    if not os.path.exists(template_path):
        raise HTTPException(status_code=500, detail="Standard template file not found")
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template_data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load template file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load template: {str(e)}")
    
    try:
        # 1. Create FlowVersion
        flow_version_data = template_data["flow_version"]
        flow_version = FlowVersion(
            company_id=current_user.company_id,
            name=flow_version_data["name"],
            description=template_data.get("description", ""),
            is_active=True,
            version_number=1
        )
        db.add(flow_version)
        db.flush()
        
        # Map stage names to stage IDs for later reference
        stage_name_to_id: Dict[str, str] = {}
        
        # 2. Create Stages and Steps
        for stage_order, stage_data in enumerate(flow_version_data["stages"], start=1):
            stage = FlowStage(
                flow_version_id=flow_version.id,
                name=stage_data["name"],
                order=stage_order
            )
            db.add(stage)
            db.flush()
            stage_name_to_id[stage_data["name"]] = stage.id
            
            # Create steps for this stage
            for step_order, step_data in enumerate(stage_data.get("steps", []), start=1):
                step = FlowStep(
                    stage_id=stage.id,
                    name=step_data["name"],
                    description=None,
                    required=step_data.get("required", False),
                    expected_phrases=step_data.get("expected_phrases", []),
                    timing_requirement=step_data.get("timing_requirement"),
                    order=step_order
                )
                db.add(step)
        
        db.flush()
        
        # 3. Create Compliance Rules
        compliance_rules_data = template_data.get("compliance_rules", [])
        created_rules = []
        
        for rule_data in compliance_rules_data:
            # Map stage names to stage IDs
            applies_to_stage_ids = []
            if rule_data.get("stages"):
                for stage_name in rule_data["stages"]:
                    if stage_name in stage_name_to_id:
                        applies_to_stage_ids.append(stage_name_to_id[stage_name])
            
            # Build params based on rule type
            rule_type = RuleType(rule_data["rule_type"])
            if rule_type == RuleType.required_phrase:
                params = {
                    "phrases": rule_data.get("phrases", []),
                    "match_type": "contains",
                    "case_sensitive": False,
                    "scope": "stage" if applies_to_stage_ids else "call"
                }
            elif rule_type == RuleType.forbidden_phrase:
                params = {
                    "phrases": rule_data.get("phrases", []),
                    "match_type": "contains",
                    "case_sensitive": False,
                    "scope": "stage" if applies_to_stage_ids else "call"
                }
            else:
                params = {}
            
            rule = ComplianceRule(
                flow_version_id=flow_version.id,
                title=rule_data["title"],
                description=rule_data.get("description", rule_data["title"]),
                severity=Severity(rule_data["severity"]),
                rule_type=rule_type,
                applies_to_stages=applies_to_stage_ids if applies_to_stage_ids else None,
                params=params,
                active=True
            )
            db.add(rule)
            created_rules.append(rule)
        
        db.flush()
        
        # 4. Create Rubric Template
        rubric_data = template_data.get("rubric_template", {})
        rubric = RubricTemplate(
            flow_version_id=flow_version.id,
            name=rubric_data.get("name", "Standard BPO QA Rubric"),
            description=rubric_data.get("description"),
            version_number=1,
            is_active=True,
            created_by_user_id=current_user.id
        )
        db.add(rubric)
        db.flush()
        
        # Create categories and mappings
        categories_data = rubric_data.get("categories", [])
        for cat_data in categories_data:
            category = RubricCategory(
                rubric_template_id=rubric.id,
                name=cat_data["name"],
                description=cat_data.get("description"),
                weight=Decimal(str(cat_data["weight"])),
                pass_threshold=cat_data.get("pass_threshold", 70),
                level_definitions=cat_data.get("levels", [])
            )
            db.add(category)
            db.flush()
            
            # Create mappings for this category
            mappings_data = cat_data.get("mappings", [])
            for mapping_data in mappings_data:
                # Map stage name to stage ID
                target_id = None
                if mapping_data["target_type"] == "stage":
                    stage_name = mapping_data["target_name"]
                    if stage_name in stage_name_to_id:
                        target_id = stage_name_to_id[stage_name]
                
                if target_id:
                    mapping = RubricMapping(
                        rubric_category_id=category.id,
                        target_type=mapping_data["target_type"],
                        target_id=target_id,
                        contribution_weight=Decimal(str(mapping_data.get("weight", 1.0))),
                        required_flag=False
                    )
                    db.add(mapping)
        
        db.commit()
        db.refresh(flow_version)
        db.refresh(rubric)
        
        # Convert to response models using model_validate (Pydantic v2) or from_orm (Pydantic v1)
        try:
            # Try Pydantic v2 style first
            flow_version_response = FlowVersionResponse.model_validate(flow_version)
            rubric_response = RubricTemplateResponse.model_validate(rubric)
        except AttributeError:
            # Fallback to Pydantic v1 style
            flow_version_response = FlowVersionResponse.from_orm(flow_version)
            rubric_response = RubricTemplateResponse.from_orm(rubric)
        
        return {
            "flow_version": flow_version_response.dict(),
            "rubric": rubric_response.dict(),
            "compliance_rules_count": len(created_rules),
            "message": "Standard template loaded successfully"
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create standard template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create template: {str(e)}")

