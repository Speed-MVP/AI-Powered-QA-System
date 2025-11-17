from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, UserRole
from app.models.policy_template import PolicyTemplate
from app.models.evaluation_criteria import EvaluationCriteria
from app.middleware.auth import get_current_user
from app.middleware.permissions import require_role
from app.schemas.policy_template import (
    PolicyTemplateCreate,
    PolicyTemplateResponse,
    EvaluationCriteriaCreate,
    EvaluationCriteriaResponse,
)
from app.schemas.rubric_level import RubricLevelCreate, RubricLevelResponse
from app.models.evaluation_rubric_level import EvaluationRubricLevel
from app.utils.validators import validate_weight_sum
from decimal import Decimal
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/prebuilt", response_model=PolicyTemplateResponse)
async def create_prebuilt_template(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create pre-built Standard QA Template with 5 criteria (admin or qa_manager only)"""
    if current_user.role not in [UserRole.admin, UserRole.qa_manager]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        from app.services.template_seeder import seed_default_template
        
        # Check if template already exists
        existing_template = db.query(PolicyTemplate).filter(
            PolicyTemplate.company_id == current_user.company_id,
            PolicyTemplate.template_name == "Standard QA Template"
        ).first()
        
        if existing_template:
            raise HTTPException(
                status_code=400,
                detail="Standard QA Template already exists for this company"
            )
        
        # Create the pre-built template
        template = seed_default_template(current_user.company_id, current_user.id, db)
        
        # Reload with criteria using joinedload
        from sqlalchemy.orm import joinedload
        template_with_criteria = db.query(PolicyTemplate).options(
            joinedload(PolicyTemplate.evaluation_criteria).joinedload(EvaluationCriteria.rubric_levels)
        ).filter(PolicyTemplate.id == template.id).first()
        
        return PolicyTemplateResponse.from_orm(template_with_criteria)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create pre-built template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create pre-built template: {str(e)}")


@router.post("", response_model=PolicyTemplateResponse)
async def create_template(
    template_data: PolicyTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new policy template (admin or qa_manager only)"""
    if current_user.role not in [UserRole.admin, UserRole.qa_manager]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Validate weights sum to 100
    if template_data.criteria:
        weights = [Decimal(str(c.weight)) for c in template_data.criteria]
        if not validate_weight_sum(weights):
            raise HTTPException(
                status_code=400,
                detail="Criteria weights must sum to 100"
            )
    
    # Create template
    template = PolicyTemplate(
        company_id=current_user.company_id,
        template_name=template_data.template_name,
        description=template_data.description,
        is_active=template_data.is_active,
        enable_structured_rules=True  # Always enable structured rules for new templates
    )
    db.add(template)
    db.flush()
    
    # Create criteria
    for criteria_data in template_data.criteria:
        criterion = EvaluationCriteria(
            policy_template_id=template.id,
            category_name=criteria_data.category_name,
            weight= Decimal(str(criteria_data.weight)),
            passing_score=criteria_data.passing_score,
            evaluation_prompt=criteria_data.evaluation_prompt
        )
        db.add(criterion)
    
    db.commit()
    db.refresh(template)
    
    # Auto-generate rules if template is created as active and has no rules
    if template.is_active and template.policy_rules is None:
        try:
            from app.services.policy_rule_builder import PolicyRuleBuilder
            from sqlalchemy.orm import joinedload
            
            # Reload template with criteria and rubric levels
            template_with_data = db.query(PolicyTemplate).options(
                joinedload(PolicyTemplate.evaluation_criteria).joinedload(EvaluationCriteria.rubric_levels)
            ).filter(PolicyTemplate.id == template.id).first()
            
            if template_with_data:
                # Extract policy text
                policy_parts = []
                if template_with_data.description:
                    policy_parts.append(template_with_data.description)
                for criterion in template_with_data.evaluation_criteria:
                    if criterion.evaluation_prompt:
                        policy_parts.append(f"{criterion.category_name}: {criterion.evaluation_prompt}")
                policy_text = "\n\n".join(policy_parts)
                
                # Extract rubric levels
                rubric_levels = {}
                for criterion in template_with_data.evaluation_criteria:
                    rubric_levels[criterion.category_name] = []
                    for level in criterion.rubric_levels:
                        rubric_levels[criterion.category_name].append({
                            "level_name": level.level_name,
                            "min_score": level.min_score,
                            "max_score": level.max_score,
                            "description": level.description
                        })
                
                if policy_text:
                    # Generate rules automatically (skip clarification step)
                    builder = PolicyRuleBuilder()
                    validated_rules, metadata = builder.generate_structured_rules(
                        policy_text=policy_text,
                        clarification_answers={},  # Empty - auto-generate without clarifications
                        rubric_levels=rubric_levels
                    )
                    
                    # Convert to dict for storage
                    rules_dict = {
                        "version": 1,
                        "rules": {
                            category: [rule.dict() for rule in rules]
                            for category, rules in validated_rules.rules.items()
                        },
                        "metadata": validated_rules.metadata
                    }
                    
                    # Save rules to template
                    template.policy_rules = rules_dict
                    template.policy_rules_version = 1
                    template.rules_generated_at = datetime.utcnow()
                    template.rules_approved_by_user_id = current_user.id
                    template.rules_generation_method = "ai"
                    template.enable_structured_rules = True
                    
                    db.commit()
                    logger.info(f"Auto-generated rules for template {template.id} when created as active")
        except Exception as e:
            logger.error(f"Failed to auto-generate rules for template {template.id}: {e}")
            # Don't fail template creation if rule generation fails
            # Template will still be created, just without structured rules
            # No rollback needed - template is already saved
    
    # Reload with criteria using joinedload
    from sqlalchemy.orm import joinedload
    template_with_criteria = db.query(PolicyTemplate).options(
        joinedload(PolicyTemplate.evaluation_criteria).joinedload(EvaluationCriteria.rubric_levels)
    ).filter(PolicyTemplate.id == template.id).first()
    
    return PolicyTemplateResponse(
        id=template_with_criteria.id,
        company_id=template_with_criteria.company_id,
        template_name=template_with_criteria.template_name,
        description=template_with_criteria.description,
        is_active=template_with_criteria.is_active,
        created_at=template_with_criteria.created_at,
        criteria=[
            EvaluationCriteriaResponse(
                id=c.id,
                category_name=c.category_name,
                weight=c.weight,
                passing_score=c.passing_score,
                evaluation_prompt=c.evaluation_prompt,
                created_at=c.created_at
            ) for c in template_with_criteria.evaluation_criteria
        ],
        policy_rules=template_with_criteria.policy_rules,
        policy_rules_version=template_with_criteria.policy_rules_version,
        enable_structured_rules=template_with_criteria.enable_structured_rules
    )


@router.get("", response_model=list[PolicyTemplateResponse])
async def list_templates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List policy templates for company"""
    from sqlalchemy.orm import joinedload
    templates = db.query(PolicyTemplate).options(
        joinedload(PolicyTemplate.evaluation_criteria)
    ).filter(
        PolicyTemplate.company_id == current_user.company_id
    ).all()
    
    # Convert to response format
    return [
        PolicyTemplateResponse(
            id=t.id,
            company_id=t.company_id,
            template_name=t.template_name,
            description=t.description,
            is_active=t.is_active,
            created_at=t.created_at,
            criteria=[
                EvaluationCriteriaResponse(
                    id=c.id,
                    category_name=c.category_name,
                    weight=c.weight,
                    passing_score=c.passing_score,
                    evaluation_prompt=c.evaluation_prompt,
                    created_at=c.created_at,
                    rubric_levels=[
                        RubricLevelResponse(
                            id=rl.id,
                            criteria_id=rl.criteria_id,
                            level_name=rl.level_name,
                            level_order=rl.level_order,
                            min_score=rl.min_score,
                            max_score=rl.max_score,
                            description=rl.description,
                            examples=rl.examples
                        ) for rl in c.rubric_levels
                    ]
                ) for c in t.evaluation_criteria
            ],
            policy_rules=t.policy_rules,
            policy_rules_version=t.policy_rules_version,
            enable_structured_rules=t.enable_structured_rules
        ) for t in templates
    ]


@router.get("/{template_id}", response_model=PolicyTemplateResponse)
async def get_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific policy template"""
    from sqlalchemy.orm import joinedload
    template = db.query(PolicyTemplate).options(
        joinedload(PolicyTemplate.evaluation_criteria).joinedload(EvaluationCriteria.rubric_levels)
    ).filter(
        PolicyTemplate.id == template_id,
        PolicyTemplate.company_id == current_user.company_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return PolicyTemplateResponse(
        id=template.id,
        company_id=template.company_id,
        template_name=template.template_name,
        description=template.description,
        is_active=template.is_active,
        created_at=template.created_at,
        criteria=[
            EvaluationCriteriaResponse(
                id=c.id,
                category_name=c.category_name,
                weight=c.weight,
                passing_score=c.passing_score,
                evaluation_prompt=c.evaluation_prompt,
                created_at=c.created_at
            ) for c in template.evaluation_criteria
        ],
        policy_rules=template.policy_rules,
        policy_rules_version=template.policy_rules_version,
        enable_structured_rules=template.enable_structured_rules
    )


@router.put("/{template_id}", response_model=PolicyTemplateResponse)
async def update_template(
    template_id: str,
    template_data: PolicyTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update policy template (admin or qa_manager only)"""
    if current_user.role not in [UserRole.admin, UserRole.qa_manager]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    template = db.query(PolicyTemplate).filter(
        PolicyTemplate.id == template_id,
        PolicyTemplate.company_id == current_user.company_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Validate weights if criteria provided
    if template_data.criteria:
        weights = [Decimal(str(c.weight)) for c in template_data.criteria]
        if not validate_weight_sum(weights):
            raise HTTPException(
                status_code=400,
                detail="Criteria weights must sum to 100"
            )
    
    # Get existing criteria with rubric levels for content comparison
    existing_criteria = db.query(EvaluationCriteria).filter(
        EvaluationCriteria.policy_template_id == template_id
    ).all()
    existing_criteria_count = len(existing_criteria)
    
    # Load rubric levels for existing criteria
    from sqlalchemy.orm import joinedload
    existing_criteria_with_levels = db.query(EvaluationCriteria).options(
        joinedload(EvaluationCriteria.rubric_levels)
    ).filter(EvaluationCriteria.policy_template_id == template_id).all()
    
    # Detect if template CONTENT has changed (not just metadata like name or is_active)
    # Content includes: description, criteria (count, names, prompts, weights, scores), rubric levels
    content_changed = False
    
    # Check description change
    if (template.description or "") != (template_data.description or ""):
        content_changed = True
    
    # Check if criteria list changed (count, content)
    if template_data.criteria is not None:
        new_criteria_list = template_data.criteria
        
        # Check if count changed
        if len(existing_criteria) != len(new_criteria_list):
            content_changed = True
        else:
            # Check if any criterion content changed
            for i, new_criteria in enumerate(new_criteria_list):
                if i < len(existing_criteria):
                    existing = existing_criteria[i]
                    if (existing.category_name != new_criteria.category_name or
                        existing.weight != Decimal(str(new_criteria.weight)) or
                        existing.passing_score != new_criteria.passing_score or
                        (existing.evaluation_prompt or "") != (new_criteria.evaluation_prompt or "")):
                        content_changed = True
                        break
                else:
                    content_changed = True
                    break
    
    # If content changed, clear existing rules (they're now stale)
    if content_changed and template.policy_rules is not None:
        template.policy_rules = None
        template.policy_rules_version = None
        template.rules_generated_at = None
        template.rules_approved_by_user_id = None
        template.rules_generation_method = None
    
    # After clearing rules if content changed, check if we need to generate new rules
    # Check if template is being activated and doesn't have rules yet
    # Also check if template is already active but has no rules (for cases where switching back)
    # Note: template.policy_rules might be None now if content_changed cleared it
    is_being_activated = template_data.is_active and not template.is_active
    is_already_active_without_rules = template_data.is_active and template.is_active and template.policy_rules is None
    has_existing_rules = template.policy_rules is not None
    needs_rule_generation = (is_being_activated or is_already_active_without_rules) and not has_existing_rules
    
    # Check if only is_active is changing (simple template switch)
    # If name/description unchanged, treat as switch and skip criteria updates
    # This prevents foreign key violations when user just wants to switch active template
    only_switching_active = (
        template.template_name == template_data.template_name and
        (template.description or "") == (template_data.description or "") and
        not content_changed
    )
    
    # If it's just a switch, we'll skip criteria updates entirely
    # User can update criteria separately if needed
    
    # Update template basic fields
    template.template_name = template_data.template_name
    template.description = template_data.description
    template.is_active = template_data.is_active
    
    # Only update criteria if we're NOT just switching active status
    # When switching templates, skip criteria updates to avoid foreign key violations
    if not only_switching_active and template_data.criteria is not None:
        new_criteria_list = template_data.criteria
        
        # Update existing criteria up to the minimum of existing and new counts
        for i, criteria_data in enumerate(new_criteria_list):
            if i < len(existing_criteria):
                # Update existing criterion
                existing_criteria[i].category_name = criteria_data.category_name
                existing_criteria[i].weight = Decimal(str(criteria_data.weight))
                existing_criteria[i].passing_score = criteria_data.passing_score
                existing_criteria[i].evaluation_prompt = criteria_data.evaluation_prompt
            else:
                # Create new criterion
                criterion = EvaluationCriteria(
                    policy_template_id=template.id,
                    category_name=criteria_data.category_name,
                    weight=Decimal(str(criteria_data.weight)),
                    passing_score=criteria_data.passing_score,
                    evaluation_prompt=criteria_data.evaluation_prompt
                )
                db.add(criterion)
        
        # Handle excess criteria (when new list is shorter than existing)
        # Only delete criteria that are not referenced by policy_violations
        if len(existing_criteria) > len(new_criteria_list):
            from app.models.policy_violation import PolicyViolation
            
            for i in range(len(new_criteria_list), len(existing_criteria)):
                criterion_to_delete = existing_criteria[i]
                # Check if criterion is referenced by policy_violations
                has_violations = db.query(PolicyViolation).filter(
                    PolicyViolation.criteria_id == criterion_to_delete.id
                ).first() is not None
                
                if not has_violations:
                    # Safe to delete - not referenced
                    db.delete(criterion_to_delete)
                else:
                    # Can't delete due to foreign key constraint
                    # If we have new criteria, update this one to match the last new criterion
                    if new_criteria_list:
                        last_criteria = new_criteria_list[-1]
                        criterion_to_delete.category_name = last_criteria.category_name
                        criterion_to_delete.weight = Decimal(str(last_criteria.weight))
                        criterion_to_delete.passing_score = last_criteria.passing_score
                        criterion_to_delete.evaluation_prompt = last_criteria.evaluation_prompt
                    # If new_criteria_list is empty, we leave the criterion as-is
                    # (can't delete it due to foreign key, but template will effectively have no active criteria)
    
    db.commit()
    db.refresh(template)
    
    # Auto-generate rules if template is being activated and has no rules
    # Check again after commit to ensure we have the latest state
    if needs_rule_generation:
        # Double-check that template still has no rules (in case it was set elsewhere)
        db.refresh(template)
        if template.policy_rules is None:
            try:
                from app.services.policy_rule_builder import PolicyRuleBuilder
                from sqlalchemy.orm import joinedload
                
                # Reload template with criteria and rubric levels
                template_with_data = db.query(PolicyTemplate).options(
                    joinedload(PolicyTemplate.evaluation_criteria).joinedload(EvaluationCriteria.rubric_levels)
                ).filter(PolicyTemplate.id == template_id).first()
                
                if template_with_data:
                    # Extract policy text
                    policy_parts = []
                    if template_with_data.description:
                        policy_parts.append(template_with_data.description)
                    for criterion in template_with_data.evaluation_criteria:
                        if criterion.evaluation_prompt:
                            policy_parts.append(f"{criterion.category_name}: {criterion.evaluation_prompt}")
                    policy_text = "\n\n".join(policy_parts)
                    
                    # Extract rubric levels
                    rubric_levels = {}
                    for criterion in template_with_data.evaluation_criteria:
                        rubric_levels[criterion.category_name] = []
                        for level in criterion.rubric_levels:
                            rubric_levels[criterion.category_name].append({
                                "level_name": level.level_name,
                                "min_score": level.min_score,
                                "max_score": level.max_score,
                                "description": level.description
                            })
                    
                    if policy_text:
                        # Generate rules automatically (skip clarification step)
                        builder = PolicyRuleBuilder()
                        validated_rules, metadata = builder.generate_structured_rules(
                            policy_text=policy_text,
                            clarification_answers={},  # Empty - auto-generate without clarifications
                            rubric_levels=rubric_levels
                        )
                        
                        # Convert to dict for storage
                        rules_dict = {
                            "version": 1,
                            "rules": {
                                category: [rule.dict() for rule in rules]
                                for category, rules in validated_rules.rules.items()
                            },
                            "metadata": validated_rules.metadata
                        }
                        
                        # Save rules to template
                        template.policy_rules = rules_dict
                        template.policy_rules_version = 1
                        template.rules_generated_at = datetime.utcnow()
                        template.rules_approved_by_user_id = current_user.id
                        template.rules_generation_method = "ai"
                        template.enable_structured_rules = True  # Enable structured rules when rules are generated
                        
                        db.commit()
                    else:
                        pass  # Policy text is empty, skip rule generation
            except Exception as e:
                logger.error(f"Failed to auto-generate rules for template {template_id}: {e}")
                # Don't fail the template update if rule generation fails
                # Template will still be activated, just without structured rules
                # No rollback needed - template update is already saved
        else:
            # If template has rules but enable_structured_rules is False, enable it
            if template.policy_rules is not None and not template.enable_structured_rules:
                template.enable_structured_rules = True
                db.commit()
    
    # Reload with criteria using joinedload
    from sqlalchemy.orm import joinedload
    template_with_criteria = db.query(PolicyTemplate).options(
        joinedload(PolicyTemplate.evaluation_criteria).joinedload(EvaluationCriteria.rubric_levels)
    ).filter(PolicyTemplate.id == template.id).first()
    
    return PolicyTemplateResponse(
        id=template_with_criteria.id,
        company_id=template_with_criteria.company_id,
        template_name=template_with_criteria.template_name,
        description=template_with_criteria.description,
        is_active=template_with_criteria.is_active,
        created_at=template_with_criteria.created_at,
        criteria=[
            EvaluationCriteriaResponse(
                id=c.id,
                category_name=c.category_name,
                weight=c.weight,
                passing_score=c.passing_score,
                evaluation_prompt=c.evaluation_prompt,
                created_at=c.created_at
            ) for c in template_with_criteria.evaluation_criteria
        ],
        policy_rules=template_with_criteria.policy_rules,
        policy_rules_version=template_with_criteria.policy_rules_version,
        enable_structured_rules=template_with_criteria.enable_structured_rules
    )


@router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete policy template (admin or qa_manager only)"""
    if current_user.role not in [UserRole.admin, UserRole.qa_manager]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    template = db.query(PolicyTemplate).filter(
        PolicyTemplate.id == template_id,
        PolicyTemplate.company_id == current_user.company_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    db.delete(template)
    db.commit()
    
    return {"message": "Template deleted successfully"}


@router.post("/{template_id}/criteria", response_model=EvaluationCriteriaResponse)
async def add_criteria(
    template_id: str,
    criteria_data: EvaluationCriteriaCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add evaluation criteria to template (admin or qa_manager only)"""
    if current_user.role not in [UserRole.admin, UserRole.qa_manager]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    template = db.query(PolicyTemplate).filter(
        PolicyTemplate.id == template_id,
        PolicyTemplate.company_id == current_user.company_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Check weight sum
    existing_criteria = db.query(EvaluationCriteria).filter(
        EvaluationCriteria.policy_template_id == template_id
    ).all()
    
    existing_weights = [c.weight for c in existing_criteria]
    new_weight = Decimal(str(criteria_data.weight))
    
    total_weight = sum(existing_weights) + new_weight
    if total_weight > Decimal("100.00"):
        raise HTTPException(
            status_code=400,
            detail=f"Adding this criteria would exceed 100% total weight (current: {sum(existing_weights)}%)"
        )
    
    # Create criteria
    criterion = EvaluationCriteria(
        policy_template_id=template_id,
        category_name=criteria_data.category_name,
        weight=new_weight,
        passing_score=criteria_data.passing_score,
        evaluation_prompt=criteria_data.evaluation_prompt
    )
    db.add(criterion)
    db.commit()
    db.refresh(criterion)
    
    # Automatically create 5 default rubric levels covering the full 0-100 range
    default_levels = [
        {
            "level_name": "Excellent",
            "level_order": 1,
            "min_score": 90,
            "max_score": 100,
            "description": "Exceeds all expectations. Perfect execution with exceptional quality.",
            "examples": None
        },
        {
            "level_name": "Good",
            "level_order": 2,
            "min_score": 70,
            "max_score": 89,
            "description": "Meets expectations consistently. Solid performance with minor areas for improvement.",
            "examples": None
        },
        {
            "level_name": "Average",
            "level_order": 3,
            "min_score": 50,
            "max_score": 69,
            "description": "Meets basic expectations. Adequate performance with noticeable areas for improvement.",
            "examples": None
        },
        {
            "level_name": "Poor",
            "level_order": 4,
            "min_score": 30,
            "max_score": 49,
            "description": "Below expectations. Significant gaps in performance requiring immediate attention.",
            "examples": None
        },
        {
            "level_name": "Unacceptable",
            "level_order": 5,
            "min_score": 0,
            "max_score": 29,
            "description": "Fails to meet minimum standards. Critical performance issues requiring intervention.",
            "examples": None
        }
    ]
    
    for level_data in default_levels:
        rubric_level = EvaluationRubricLevel(
            criteria_id=criterion.id,
            level_name=level_data["level_name"],
            level_order=level_data["level_order"],
            min_score=level_data["min_score"],
            max_score=level_data["max_score"],
            description=level_data["description"],
            examples=level_data["examples"]
        )
        db.add(rubric_level)
    
    db.commit()
    
    # Load rubric_levels relationship for proper serialization
    from sqlalchemy.orm import joinedload
    criterion_with_levels = db.query(EvaluationCriteria).options(
        joinedload(EvaluationCriteria.rubric_levels)
    ).filter(EvaluationCriteria.id == criterion.id).first()
    
    return criterion_with_levels


@router.put("/{template_id}/criteria/{criteria_id}", response_model=EvaluationCriteriaResponse)
async def update_criteria(
    template_id: str,
    criteria_id: str,
    criteria_data: EvaluationCriteriaCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update evaluation criteria (admin or qa_manager only)"""
    if current_user.role not in [UserRole.admin, UserRole.qa_manager]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Verify template belongs to user's company
    template = db.query(PolicyTemplate).filter(
        PolicyTemplate.id == template_id,
        PolicyTemplate.company_id == current_user.company_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Get criteria
    criterion = db.query(EvaluationCriteria).filter(
        EvaluationCriteria.id == criteria_id,
        EvaluationCriteria.policy_template_id == template_id
    ).first()
    
    if not criterion:
        raise HTTPException(status_code=404, detail="Criteria not found")
    
    # Check weight sum (excluding current criteria)
    existing_criteria = db.query(EvaluationCriteria).filter(
        EvaluationCriteria.policy_template_id == template_id,
        EvaluationCriteria.id != criteria_id
    ).all()
    
    existing_weights = [c.weight for c in existing_criteria]
    new_weight = Decimal(str(criteria_data.weight))
    
    total_weight = sum(existing_weights) + new_weight
    if total_weight > Decimal("100.00"):
        raise HTTPException(
            status_code=400,
            detail=f"Updating this criteria would exceed 100% total weight (current without this: {sum(existing_weights)}%)"
        )
    
    # Update criteria
    criterion.category_name = criteria_data.category_name
    criterion.weight = new_weight
    criterion.passing_score = criteria_data.passing_score
    criterion.evaluation_prompt = criteria_data.evaluation_prompt
    
    db.commit()
    db.refresh(criterion)
    
    # Load rubric_levels relationship for proper serialization
    from sqlalchemy.orm import joinedload
    criterion_with_levels = db.query(EvaluationCriteria).options(
        joinedload(EvaluationCriteria.rubric_levels)
    ).filter(EvaluationCriteria.id == criteria_id).first()
    
    return criterion_with_levels


@router.post("/{template_id}/generate-rules")
async def generate_rules_for_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Temporary endpoint to manually generate policy rules for a template"""
    if current_user.role not in [UserRole.admin, UserRole.qa_manager]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    template = db.query(PolicyTemplate).filter(
        PolicyTemplate.id == template_id,
        PolicyTemplate.company_id == current_user.company_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    try:
        from app.services.policy_rule_builder import PolicyRuleBuilder
        from sqlalchemy.orm import joinedload
        
        # Reload template with criteria and rubric levels
        template_with_data = db.query(PolicyTemplate).options(
            joinedload(PolicyTemplate.evaluation_criteria).joinedload(EvaluationCriteria.rubric_levels)
        ).filter(PolicyTemplate.id == template_id).first()
        
        if not template_with_data:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Extract policy text
        policy_parts = []
        if template_with_data.description:
            policy_parts.append(template_with_data.description)
        for criterion in template_with_data.evaluation_criteria:
            if criterion.evaluation_prompt:
                policy_parts.append(f"{criterion.category_name}: {criterion.evaluation_prompt}")
        policy_text = "\n\n".join(policy_parts)
        
        # Extract rubric levels
        rubric_levels = {}
        for criterion in template_with_data.evaluation_criteria:
            rubric_levels[criterion.category_name] = []
            for level in criterion.rubric_levels:
                rubric_levels[criterion.category_name].append({
                    "level_name": level.level_name,
                    "min_score": level.min_score,
                    "max_score": level.max_score,
                    "description": level.description
                })
        
        if not policy_text:
            raise HTTPException(
                status_code=400,
                detail="Template has no description or evaluation prompts. Cannot generate rules."
            )
        
        # Generate rules automatically (skip clarification step)
        builder = PolicyRuleBuilder()
        validated_rules, metadata = builder.generate_structured_rules(
            policy_text=policy_text,
            clarification_answers={},  # Empty - auto-generate without clarifications
            rubric_levels=rubric_levels
        )
        
        # Convert to dict for storage
        rules_dict = {
            "version": 1,
            "rules": {
                category: [rule.dict() for rule in rules]
                for category, rules in validated_rules.rules.items()
            },
            "metadata": validated_rules.metadata
        }
        
        # Save rules to template
        template.policy_rules = rules_dict
        template.policy_rules_version = 1
        template.rules_generated_at = datetime.utcnow()
        template.rules_approved_by_user_id = current_user.id
        template.rules_generation_method = "ai"
        template.enable_structured_rules = True
        
        db.commit()
        
        return {
            "success": True,
            "message": "Policy rules generated successfully",
            "rules_version": template.policy_rules_version,
            "categories": list(rules_dict.get('rules', {}).keys())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate rules for template {template_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate rules: {str(e)}"
        )


@router.delete("/{template_id}/criteria/{criteria_id}")
async def delete_criteria(
    template_id: str,
    criteria_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete evaluation criteria (admin or qa_manager only)"""
    if current_user.role not in [UserRole.admin, UserRole.qa_manager]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Verify template belongs to user's company
    template = db.query(PolicyTemplate).filter(
        PolicyTemplate.id == template_id,
        PolicyTemplate.company_id == current_user.company_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Get criteria
    criterion = db.query(EvaluationCriteria).filter(
        EvaluationCriteria.id == criteria_id,
        EvaluationCriteria.policy_template_id == template_id
    ).first()
    
    if not criterion:
        raise HTTPException(status_code=404, detail="Criteria not found")
    
    # Delete criteria
    db.delete(criterion)
    db.commit()
    
    return {"message": "Criteria deleted successfully"}


@router.post("/{template_id}/criteria/{criteria_id}/rubric-levels", response_model=RubricLevelResponse)
async def add_rubric_level(
    template_id: str,
    criteria_id: str,
    level_data: RubricLevelCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add rubric level to evaluation criteria (admin or qa_manager only)"""
    if current_user.role not in [UserRole.admin, UserRole.qa_manager]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Verify template and criteria belong to user's company
    template = db.query(PolicyTemplate).filter(
        PolicyTemplate.id == template_id,
        PolicyTemplate.company_id == current_user.company_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    criterion = db.query(EvaluationCriteria).filter(
        EvaluationCriteria.id == criteria_id,
        EvaluationCriteria.policy_template_id == template_id
    ).first()
    
    if not criterion:
        raise HTTPException(status_code=404, detail="Criteria not found")
    
    # Validate score range
    if level_data.min_score < 0 or level_data.max_score > 100:
        raise HTTPException(status_code=400, detail="Scores must be between 0 and 100")
    
    if level_data.min_score > level_data.max_score:
        raise HTTPException(status_code=400, detail="min_score must be less than or equal to max_score")
    
    # Check for overlapping score ranges
    existing_levels = db.query(EvaluationRubricLevel).filter(
        EvaluationRubricLevel.criteria_id == criteria_id
    ).all()
    
    for existing in existing_levels:
        if not (level_data.max_score < existing.min_score or level_data.min_score > existing.max_score):
            raise HTTPException(
                status_code=400,
                detail=f"Score range overlaps with existing level '{existing.level_name}' ({existing.min_score}-{existing.max_score})"
            )
    
    # Create rubric level
    rubric_level = EvaluationRubricLevel(
        criteria_id=criteria_id,
        level_name=level_data.level_name,
        level_order=level_data.level_order,
        min_score=level_data.min_score,
        max_score=level_data.max_score,
        description=level_data.description,
        examples=level_data.examples
    )
    db.add(rubric_level)
    db.commit()
    db.refresh(rubric_level)
    
    return RubricLevelResponse(
        id=rubric_level.id,
        criteria_id=rubric_level.criteria_id,
        level_name=rubric_level.level_name,
        level_order=rubric_level.level_order,
        min_score=rubric_level.min_score,
        max_score=rubric_level.max_score,
        description=rubric_level.description,
        examples=rubric_level.examples
    )


@router.put("/{template_id}/criteria/{criteria_id}/rubric-levels/{level_id}", response_model=RubricLevelResponse)
async def update_rubric_level(
    template_id: str,
    criteria_id: str,
    level_id: str,
    level_data: RubricLevelCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update rubric level (admin or qa_manager only)"""
    if current_user.role not in [UserRole.admin, UserRole.qa_manager]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Verify template and criteria belong to user's company
    template = db.query(PolicyTemplate).filter(
        PolicyTemplate.id == template_id,
        PolicyTemplate.company_id == current_user.company_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    criterion = db.query(EvaluationCriteria).filter(
        EvaluationCriteria.id == criteria_id,
        EvaluationCriteria.policy_template_id == template_id
    ).first()
    
    if not criterion:
        raise HTTPException(status_code=404, detail="Criteria not found")
    
    rubric_level = db.query(EvaluationRubricLevel).filter(
        EvaluationRubricLevel.id == level_id,
        EvaluationRubricLevel.criteria_id == criteria_id
    ).first()
    
    if not rubric_level:
        raise HTTPException(status_code=404, detail="Rubric level not found")
    
    # Validate score range
    if level_data.min_score < 0 or level_data.max_score > 100:
        raise HTTPException(status_code=400, detail="Scores must be between 0 and 100")
    
    if level_data.min_score > level_data.max_score:
        raise HTTPException(status_code=400, detail="min_score must be less than or equal to max_score")
    
    # Check for overlapping score ranges (excluding current level)
    existing_levels = db.query(EvaluationRubricLevel).filter(
        EvaluationRubricLevel.criteria_id == criteria_id,
        EvaluationRubricLevel.id != level_id
    ).all()
    
    for existing in existing_levels:
        if not (level_data.max_score < existing.min_score or level_data.min_score > existing.max_score):
            raise HTTPException(
                status_code=400,
                detail=f"Score range overlaps with existing level '{existing.level_name}' ({existing.min_score}-{existing.max_score})"
            )
    
    # Update rubric level
    rubric_level.level_name = level_data.level_name
    rubric_level.level_order = level_data.level_order
    rubric_level.min_score = level_data.min_score
    rubric_level.max_score = level_data.max_score
    rubric_level.description = level_data.description
    rubric_level.examples = level_data.examples
    
    db.commit()
    db.refresh(rubric_level)
    
    return RubricLevelResponse(
        id=rubric_level.id,
        criteria_id=rubric_level.criteria_id,
        level_name=rubric_level.level_name,
        level_order=rubric_level.level_order,
        min_score=rubric_level.min_score,
        max_score=rubric_level.max_score,
        description=rubric_level.description,
        examples=rubric_level.examples
    )


@router.delete("/{template_id}/criteria/{criteria_id}/rubric-levels/{level_id}")
async def delete_rubric_level(
    template_id: str,
    criteria_id: str,
    level_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete rubric level (admin or qa_manager only)"""
    if current_user.role not in [UserRole.admin, UserRole.qa_manager]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Verify template and criteria belong to user's company
    template = db.query(PolicyTemplate).filter(
        PolicyTemplate.id == template_id,
        PolicyTemplate.company_id == current_user.company_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    criterion = db.query(EvaluationCriteria).filter(
        EvaluationCriteria.id == criteria_id,
        EvaluationCriteria.policy_template_id == template_id
    ).first()
    
    if not criterion:
        raise HTTPException(status_code=404, detail="Criteria not found")
    
    rubric_level = db.query(EvaluationRubricLevel).filter(
        EvaluationRubricLevel.id == level_id,
        EvaluationRubricLevel.criteria_id == criteria_id
    ).first()
    
    if not rubric_level:
        raise HTTPException(status_code=404, detail="Rubric level not found")
    
    db.delete(rubric_level)
    db.commit()
    
    return {"message": "Rubric level deleted successfully"}

