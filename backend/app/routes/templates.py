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
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


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
        is_active=template_data.is_active
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
        ]
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
            ]
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
        ]
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
    
    # Update template
    template.template_name = template_data.template_name
    template.description = template_data.description
    template.is_active = template_data.is_active
    
    # Delete existing criteria
    db.query(EvaluationCriteria).filter(
        EvaluationCriteria.policy_template_id == template_id
    ).delete()
    
    # Create new criteria
    for criteria_data in template_data.criteria:
        criterion = EvaluationCriteria(
            policy_template_id=template.id,
            category_name=criteria_data.category_name,
            weight=Decimal(str(criteria_data.weight)),
            passing_score=criteria_data.passing_score,
            evaluation_prompt=criteria_data.evaluation_prompt
        )
        db.add(criterion)
    
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
        ]
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

