"""
Policy Rules API Routes
Phase 2: AI Policy Rule Builder

Endpoints for policy rule generation workflow:
- Analyze policy text
- Generate clarifying questions
- Submit clarification answers
- Generate structured rules
- Approve rules
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.policy_template import PolicyTemplate
from app.models.policy_clarification import PolicyClarification
from app.models.user import User, UserRole
from app.middleware.auth import get_current_user
from app.services.policy_rule_builder import PolicyRuleBuilder
from app.schemas.policy_rules import PolicyRulesSchema
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter(tags=["policy-rules"])


# Request/Response models
class AnalyzePolicyRequest(BaseModel):
    policy_text: Optional[str] = None  # If None, extract from template


class ClarificationAnswer(BaseModel):
    question_id: str
    answer: str


class SubmitClarificationsRequest(BaseModel):
    answers: List[ClarificationAnswer]


class GenerateRulesRequest(BaseModel):
    clarification_answers: Dict[str, str]


class ApproveRulesRequest(BaseModel):
    rules: Dict[str, Any]  # PolicyRulesSchema as dict


@router.post("/{template_id}/analyze-policy")
async def analyze_policy(
    template_id: str,
    request: AnalyzePolicyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Stage 1: Analyze policy text and identify vague statements.
    Admin or QA Manager only.
    """
    if current_user.role not in [UserRole.admin, UserRole.qa_manager]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    # Get policy template
    template = db.query(PolicyTemplate).filter(
        PolicyTemplate.id == template_id,
        PolicyTemplate.company_id == current_user.company_id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy template not found"
        )
    
    # Extract policy text if not provided
    policy_text = request.policy_text
    if not policy_text:
        # Extract from template description and criteria
        policy_parts = []
        if template.description:
            policy_parts.append(template.description)
        for criterion in template.evaluation_criteria:
            if criterion.evaluation_prompt:
                policy_parts.append(f"{criterion.category_name}: {criterion.evaluation_prompt}")
        policy_text = "\n\n".join(policy_parts)
    
    if not policy_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No policy text found in template and none provided"
        )
    
    # Extract rubric levels
    rubric_levels = {}
    for criterion in template.evaluation_criteria:
        rubric_levels[criterion.category_name] = []
        for level in criterion.rubric_levels:
            rubric_levels[criterion.category_name].append({
                "level_name": level.level_name,
                "min_score": level.min_score,
                "max_score": level.max_score,
                "description": level.description
            })
    
    # Analyze policy
    builder = PolicyRuleBuilder()
    try:
        analysis_results = builder.analyze_policy_text(
            policy_text=policy_text,
            rubric_levels=rubric_levels
        )
        
        # Generate clarifying questions
        clarifications = builder.generate_clarifying_questions(
            policy_text=policy_text,
            analysis_results=analysis_results,
            rubric_levels=rubric_levels
        )
        
        # Store clarifications in database
        for clarification in clarifications:
            existing = db.query(PolicyClarification).filter(
                PolicyClarification.policy_template_id == template_id,
                PolicyClarification.question_id == clarification["id"]
            ).first()
            
            if not existing:
                db_clarification = PolicyClarification(
                    policy_template_id=template_id,
                    question_id=clarification["id"],
                    question=clarification["question"],
                    status="pending"
                )
                db.add(db_clarification)
        
        db.commit()
        
        return {
            "analysis": analysis_results,
            "clarifications": clarifications
        }
        
    except Exception as e:
        logger.error(f"Policy analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Policy analysis failed: {str(e)}"
        )


@router.get("/{template_id}/clarifications")
async def get_clarifications(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get pending clarification questions for a policy template."""
    template = db.query(PolicyTemplate).filter(
        PolicyTemplate.id == template_id,
        PolicyTemplate.company_id == current_user.company_id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy template not found"
        )
    
    clarifications = db.query(PolicyClarification).filter(
        PolicyClarification.policy_template_id == template_id
    ).order_by(PolicyClarification.created_at).all()
    
    return {
        "clarifications": [
            {
                "id": c.id,
                "question_id": c.question_id,
                "question": c.question,
                "answer": c.answer,
                "status": c.status,
                "answered_at": c.answered_at.isoformat() if c.answered_at else None
            }
            for c in clarifications
        ]
    }


@router.post("/{template_id}/clarifications")
async def submit_clarifications(
    template_id: str,
    request: SubmitClarificationsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Stage 3: Submit answers to clarification questions.
    Admin or QA Manager only.
    """
    if current_user.role not in [UserRole.admin, UserRole.qa_manager]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
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
    
    # Update clarification answers
    for answer_data in request.answers:
        clarification = db.query(PolicyClarification).filter(
            PolicyClarification.policy_template_id == template_id,
            PolicyClarification.question_id == answer_data.question_id
        ).first()
        
        if clarification:
            clarification.answer = answer_data.answer
            clarification.answered_by_user_id = current_user.id
            clarification.answered_at = datetime.utcnow()
            clarification.status = "answered"
    
    db.commit()
    
    return {"message": "Clarifications submitted successfully"}


@router.post("/{template_id}/generate-rules")
async def generate_rules(
    template_id: str,
    request: GenerateRulesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Stage 4: Generate structured rules from policy + clarification answers.
    Admin or QA Manager only.
    """
    if current_user.role not in [UserRole.admin, UserRole.qa_manager]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
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
    
    # Extract policy text
    policy_parts = []
    if template.description:
        policy_parts.append(template.description)
    for criterion in template.evaluation_criteria:
        if criterion.evaluation_prompt:
            policy_parts.append(f"{criterion.category_name}: {criterion.evaluation_prompt}")
    policy_text = "\n\n".join(policy_parts)
    
    # Extract rubric levels
    rubric_levels = {}
    for criterion in template.evaluation_criteria:
        rubric_levels[criterion.category_name] = []
        for level in criterion.rubric_levels:
            rubric_levels[criterion.category_name].append({
                "level_name": level.level_name,
                "min_score": level.min_score,
                "max_score": level.max_score,
                "description": level.description
            })
    
    # Generate structured rules
    builder = PolicyRuleBuilder()
    try:
        validated_rules, metadata = builder.generate_structured_rules(
            policy_text=policy_text,
            clarification_answers=request.clarification_answers,
            rubric_levels=rubric_levels
        )
        
        # Convert to dict for storage
        rules_dict = {
            "version": validated_rules.version,
            "rules": {
                category: [rule.dict() for rule in rules]
                for category, rules in validated_rules.rules.items()
            },
            "metadata": validated_rules.metadata
        }
        
        return {
            "rules": rules_dict,
            "metadata": metadata,
            "conflicts": metadata.get("conflicts_detected", [])
        }
        
    except Exception as e:
        logger.error(f"Rule generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rule generation failed: {str(e)}"
        )


@router.post("/{template_id}/approve-rules")
async def approve_rules(
    template_id: str,
    request: ApproveRulesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Stage 5: Admin approves and locks structured rules.
    Admin only.
    """
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can approve rules"
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
    
    # Validate rules
    builder = PolicyRuleBuilder()
    try:
        validated_rules = PolicyRulesSchema(**request.rules)
        is_valid, errors = builder.validate_rules(validated_rules)
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Rules validation failed: {errors}"
            )
        
        # Update template with approved rules
        template.policy_rules = request.rules
        template.policy_rules_version = (template.policy_rules_version or 0) + 1
        template.rules_generated_at = datetime.utcnow()
        template.rules_approved_by_user_id = current_user.id
        template.rules_generation_method = "ai"
        template.enable_structured_rules = True
        
        db.commit()
        
        return {
            "message": "Rules approved and locked successfully",
            "rules_version": template.policy_rules_version
        }
        
    except Exception as e:
        logger.error(f"Rule approval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Rule approval failed: {str(e)}"
        )

