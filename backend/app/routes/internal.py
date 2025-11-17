"""
Phase 1: Structured Rules Layer - Internal API Endpoints
Deterministic QA System Redesign

Internal-only endpoints for managing policy rules.
Requires service token or admin/QA manager authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.policy_template import PolicyTemplate
from app.middleware.auth import get_current_user
from app.services.policy_rules_validator import PolicyRulesValidator, ValidationError
from app.tasks.generate_policy_rules_job import generate_policy_rules_task, clarify_policy_rules_task, policy_rules_job
from app.models.policy_rules_draft import PolicyRulesDraft, DraftStatus
from app.models.policy_rules_version import PolicyRulesVersion
from app.models.policy_template import PolicyTemplate
from app.services.deterministic_llm_evaluator import DeterministicLLMEvaluator, LLMEvaluationInput
from app.services.deterministic_scorer import DeterministicScorer
from app.services.policy_rules_versioning import PolicyRulesVersioningService
from app.services.policy_rules_sandbox import PolicyRulesSandboxService
from app.models.evaluation import Evaluation
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/internal", tags=["internal"])

# Initialize validator service
validator = PolicyRulesValidator()


def require_internal_access(current_user: User = Depends(get_current_user)) -> User:
    """
    Require internal access - only admins and QA managers, or service accounts.
    In production, this would also check for service tokens.
    """
    if current_user.role not in ["admin", "qa_manager"]:
        raise HTTPException(
            status_code=403,
            detail="Internal API access required"
        )
    return current_user


@router.post("/policy_templates/{template_id}/rules")
async def set_policy_rules(
    template_id: str,
    rules_data: dict,
    current_user: User = Depends(require_internal_access),
    db: Session = Depends(get_db)
):
    """
    Set policy rules for a policy template (internal only).

    Validates rules, stores in database, and returns normalized rules.
    Audits all changes.
    """
    logger.info(f"User {current_user.id} setting policy rules for template {template_id}")

    # Get and validate template
    template = db.query(PolicyTemplate).filter(
        PolicyTemplate.id == template_id,
        PolicyTemplate.company_id == current_user.company_id
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="Policy template not found")

    # Check authorization
    if not validator.is_editable_by_user(current_user, template.company_id):
        raise HTTPException(status_code=403, detail="Not authorized to edit policy rules")

    # Validate payload size
    if not validator.validate_rule_payload_size(rules_data):
        raise HTTPException(status_code=400, detail="Policy rules payload too large (max 50KB)")

    try:
        # Validate and normalize rules
        normalized_rules = validator.validate_policy_rules(rules_data)

        # Serialize back to JSON for storage
        serialized_rules = validator.serialize_policy_rules(normalized_rules)

        # Store in database
        template.policy_rules = serialized_rules
        db.commit()

        # Audit log (in production, this would be more comprehensive)
        logger.info(f"Policy rules updated for template {template_id} by user {current_user.id}")

        return {
            "success": True,
            "template_id": template_id,
            "rules": serialized_rules,
            "rule_count": sum(len(rules) for rules in normalized_rules.rules.values())
        }

    except ValidationError as e:
        logger.warning(f"Policy rules validation failed for template {template_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to set policy rules for template {template_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/policy_templates/{template_id}/rules")
async def get_policy_rules(
    template_id: str,
    current_user: User = Depends(require_internal_access),
    db: Session = Depends(get_db)
):
    """
    Get policy rules for a policy template (internal only).

    Returns normalized rules JSON.
    """
    # Get template
    template = db.query(PolicyTemplate).filter(
        PolicyTemplate.id == template_id,
        PolicyTemplate.company_id == current_user.company_id
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="Policy template not found")

    # Return rules (or empty object if none set)
    rules = template.policy_rules or {"rules": {}}

    return {
        "template_id": template_id,
        "rules": rules,
        "has_rules": bool(template.policy_rules)
    }


@router.get("/policy_templates/{template_id}/rule_schema")
async def get_rule_schema(
    template_id: str,
    current_user: User = Depends(require_internal_access),
    db: Session = Depends(get_db)
):
    """
    Get JSON schema for policy rules validation (internal only).

    Used by clients for form validation and documentation.
    """
    # Verify template exists and user has access
    template = db.query(PolicyTemplate).filter(
        PolicyTemplate.id == template_id,
        PolicyTemplate.company_id == current_user.company_id
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="Policy template not found")

    schema = validator.get_schema()

    return {
        "template_id": template_id,
        "schema": schema,
        "supported_rule_types": ["boolean", "numeric", "list"],
        "supported_comparators": ["le", "lt", "eq", "ge", "gt"]
    }


@router.delete("/policy_templates/{template_id}/rules")
async def delete_policy_rules(
    template_id: str,
    current_user: User = Depends(require_internal_access),
    db: Session = Depends(get_db)
):
    """
    Delete policy rules for a policy template (internal only).

    Sets policy_rules to NULL.
    """
    logger.info(f"User {current_user.id} deleting policy rules for template {template_id}")

    # Get and validate template
    template = db.query(PolicyTemplate).filter(
        PolicyTemplate.id == template_id,
        PolicyTemplate.company_id == current_user.company_id
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="Policy template not found")

    # Check authorization
    if not validator.is_editable_by_user(current_user, template.company_id):
        raise HTTPException(status_code=403, detail="Not authorized to edit policy rules")

    # Clear rules
    old_rules = template.policy_rules
    template.policy_rules = None
    db.commit()

    # Audit log
    logger.info(f"Policy rules cleared for template {template_id} by user {current_user.id}")

    return {
        "success": True,
        "template_id": template_id,
        "message": "Policy rules cleared",
        "had_rules": bool(old_rules)
    }


# Phase 2: Policy Rule Builder Endpoints

@router.post("/policy_templates/{template_id}/generate_rules")
async def generate_policy_rules(
    template_id: str,
    request: dict,
    current_user: User = Depends(require_internal_access),
    db: Session = Depends(get_db)
):
    """
    Start async generation of policy rules from human-written text (Phase 2).

    Creates a draft and enqueues background job for LLM processing.
    """
    logger.info(f"User {current_user.id} starting rule generation for template {template_id}")

    # Validate template access
    template = db.query(PolicyTemplate).filter(
        PolicyTemplate.id == template_id,
        PolicyTemplate.company_id == current_user.company_id
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="Policy template not found")

    # Validate request data
    policy_text = request.get("policy_text", "").strip()
    if not policy_text:
        raise HTTPException(status_code=400, detail="policy_text is required")

    # Create draft
    draft = PolicyRulesDraft(
        policy_template_id=template_id,
        status=DraftStatus.generating,
        policy_text=policy_text,
        rubric_levels=request.get("rubric_levels"),
        examples=request.get("examples"),
        created_by_user_id=current_user.id
    )

    db.add(draft)
    db.commit()
    db.refresh(draft)

    # Enqueue background job (in production, use proper task queue)
    try:
        # For now, run synchronously - in production this would be async
        import asyncio
        asyncio.create_task(generate_policy_rules_task(draft.id))

        logger.info(f"Enqueued rule generation job for draft {draft.id}")

    except Exception as e:
        logger.error(f"Failed to enqueue job for draft {draft.id}: {e}")
        # Continue - job status will show as failed

    return {
        "success": True,
        "draft_id": draft.id,
        "job_status": "enqueued",
        "message": "Policy rule generation started"
    }


@router.get("/policy_templates/{template_id}/drafts/{draft_id}")
async def get_draft(
    template_id: str,
    draft_id: str,
    current_user: User = Depends(require_internal_access),
    db: Session = Depends(get_db)
):
    """
    Get draft status and content (Phase 2).
    """
    # Validate template access
    template = db.query(PolicyTemplate).filter(
        PolicyTemplate.id == template_id,
        PolicyTemplate.company_id == current_user.company_id
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="Policy template not found")

    # Get draft
    draft = db.query(PolicyRulesDraft).filter(
        PolicyRulesDraft.id == draft_id,
        PolicyRulesDraft.policy_template_id == template_id
    ).first()

    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    return {
        "draft_id": draft.id,
        "template_id": draft.policy_template_id,
        "status": draft.status.value,
        "policy_text": draft.policy_text,
        "rubric_levels": draft.rubric_levels,
        "examples": draft.examples,
        "generated_rules": draft.generated_rules,
        "clarifications": draft.clarifications,
        "user_answers": draft.user_answers,
        "validation_errors": draft.validation_errors,
        "llm_model": draft.llm_model,
        "llm_tokens_used": draft.llm_tokens_used,
        "llm_latency_ms": draft.llm_latency_ms,
        "llm_prompt_hash": draft.llm_prompt_hash,
        "created_at": draft.created_at.isoformat(),
        "updated_at": draft.updated_at.isoformat()
    }


@router.post("/policy_templates/{template_id}/drafts/{draft_id}/clarify")
async def clarify_draft(
    template_id: str,
    draft_id: str,
    request: dict,
    current_user: User = Depends(require_internal_access),
    db: Session = Depends(get_db)
):
    """
    Provide answers to clarification questions and re-generate rules (Phase 2).
    """
    logger.info(f"User {current_user.id} clarifying draft {draft_id}")

    # Validate template access
    template = db.query(PolicyTemplate).filter(
        PolicyTemplate.id == template_id,
        PolicyTemplate.company_id == current_user.company_id
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="Policy template not found")

    # Get draft
    draft = db.query(PolicyRulesDraft).filter(
        PolicyRulesDraft.id == draft_id,
        PolicyRulesDraft.policy_template_id == template_id
    ).first()

    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    if draft.status != DraftStatus.needs_clarification:
        raise HTTPException(status_code=400, detail="Draft does not need clarification")

    # Validate answers
    user_answers = request.get("answers", {})
    if not isinstance(user_answers, dict):
        raise HTTPException(status_code=400, detail="answers must be a dictionary")

    # Enqueue clarification job
    try:
        import asyncio
        asyncio.create_task(clarify_policy_rules_task(draft.id, user_answers))

        logger.info(f"Enqueued clarification job for draft {draft.id}")

    except Exception as e:
        logger.error(f"Failed to enqueue clarification job for draft {draft.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to process clarification")

    return {
        "success": True,
        "draft_id": draft.id,
        "message": "Clarification answers submitted, re-generation started"
    }


@router.post("/policy_templates/{template_id}/confirm_rules")
async def confirm_policy_rules(
    template_id: str,
    request: dict,
    current_user: User = Depends(require_internal_access),
    db: Session = Depends(get_db)
):
    """
    Confirm and finalize generated policy rules (Phase 2).

    Validates rules and creates a new version in policy_rules_versions table.
    Copies rules to policy_templates.policy_rules for immediate use.
    """
    logger.info(f"User {current_user.id} confirming rules for template {template_id}")

    draft_id = request.get("draft_id")
    if not draft_id:
        raise HTTPException(status_code=400, detail="draft_id is required")

    # Validate template access
    template = db.query(PolicyTemplate).filter(
        PolicyTemplate.id == template_id,
        PolicyTemplate.company_id == current_user.company_id
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="Policy template not found")

    # Get draft
    draft = db.query(PolicyRulesDraft).filter(
        PolicyRulesDraft.id == draft_id,
        PolicyRulesDraft.policy_template_id == template_id,
        PolicyRulesDraft.status == DraftStatus.ready_for_confirm
    ).first()

    if not draft:
        raise HTTPException(status_code=404, detail="Valid draft not found")

    # Validate rules one more time
    is_valid, normalized_rules, validation_errors = validator.validate_generated_rules(draft.generated_rules)

    if not is_valid:
        # Update draft status
        draft.status = DraftStatus.validation_failed
        draft.validation_errors = validation_errors
        db.commit()

        raise HTTPException(status_code=400, detail=f"Rules validation failed: {validation_errors}")

    # Get next version number
    last_version = db.query(PolicyRulesVersion).filter(
        PolicyRulesVersion.policy_template_id == template_id
    ).order_by(PolicyRulesVersion.rules_version.desc()).first()

    next_version = (last_version.rules_version + 1) if last_version else 1

    # Create version record
    version = PolicyRulesVersion(
        policy_template_id=template_id,
        rules_version=next_version,
        policy_rules=validator.serialize_policy_rules(normalized_rules)["rules"],
        draft_id=draft_id,
        llm_model=draft.llm_model,
        llm_prompt_hash=getattr(draft, 'llm_prompt_hash', None),  # Would be set by job
        created_by_user_id=current_user.id
    )

    db.add(version)

    # Update template with new rules
    template.policy_rules = version.policy_rules

    # Mark draft as confirmed
    draft.status = DraftStatus.confirmed

    db.commit()

    # Audit log
    logger.info(f"Policy rules version {next_version} created for template {template_id} by user {current_user.id}")

    return {
        "success": True,
        "template_id": template_id,
        "rules_version": next_version,
        "draft_id": draft_id,
        "rules_count": sum(len(rules) for rules in normalized_rules.rules.values()),
        "categories": list(normalized_rules.rules.keys()),
        "message": f"Policy rules version {next_version} confirmed and activated"
    }


@router.get("/policy_templates/{template_id}/versions")
async def list_policy_rule_versions(
    template_id: str,
    current_user: User = Depends(require_internal_access),
    db: Session = Depends(get_db)
):
    """
    List all versions of policy rules for a template (Phase 2).
    """
    # Validate template access
    template = db.query(PolicyTemplate).filter(
        PolicyTemplate.id == template_id,
        PolicyTemplate.company_id == current_user.company_id
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="Policy template not found")

    versions = db.query(PolicyRulesVersion).filter(
        PolicyRulesVersion.policy_template_id == template_id
    ).order_by(PolicyRulesVersion.rules_version.desc()).all()

    return {
        "template_id": template_id,
        "versions": [
            {
                "version": v.rules_version,
                "created_at": v.created_at.isoformat(),
                "created_by": v.created_by_user_id,
                "llm_model": v.llm_model,
                "draft_id": v.draft_id,
                "rules_count": sum(len(rules) for rules in v.policy_rules.values()) if v.policy_rules else 0
            }
            for v in versions
        ]
    }


@router.get("/policy_templates/{template_id}/drafts")
async def list_drafts(
    template_id: str,
    current_user: User = Depends(require_internal_access),
    db: Session = Depends(get_db)
):
    """
    List all drafts for a policy template (Phase 2).
    """
    # Validate template access
    template = db.query(PolicyTemplate).filter(
        PolicyTemplate.id == template_id,
        PolicyTemplate.company_id == current_user.company_id
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="Policy template not found")

    drafts = db.query(PolicyRulesDraft).filter(
        PolicyRulesDraft.policy_template_id == template_id
    ).order_by(PolicyRulesDraft.created_at.desc()).all()

    return {
        "template_id": template_id,
        "drafts": [
            {
                "id": d.id,
                "status": d.status.value,
                "created_at": d.created_at.isoformat(),
                "updated_at": d.updated_at.isoformat(),
                "llm_model": d.llm_model,
                "has_clarifications": bool(d.clarifications),
                "is_validated": d.status == DraftStatus.ready_for_confirm
            }
            for d in drafts
        ]
    }


# Phase 4: Deterministic LLM Evaluator Endpoints

@router.post("/evaluations/{evaluation_id}/run_llm")
async def run_deterministic_llm_evaluation(
    evaluation_id: str,
    request: dict,
    current_user: User = Depends(require_internal_access),
    db: Session = Depends(get_db)
):
    """
    Run deterministic LLM evaluation for rubric-level classification (Phase 4).

    This endpoint replaces subjective LLM interpretation with structured rubric classification.
    """
    logger.info(f"User {current_user.id} running deterministic LLM evaluation for {evaluation_id}")

    # Validate evaluation exists and user has access
    evaluation = db.query(Evaluation).filter(
        Evaluation.id == evaluation_id,
        Evaluation.company_id == current_user.company_id
    ).first()

    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    try:
        # Build structured input from request
        evaluation_input = LLMEvaluationInput(
            evaluation_id=request["evaluation_id"],
            policy_template_id=request["policy_template_id"],
            policy_rules_version=request.get("policy_rules_version"),
            categories=request["categories"],
            rubric_levels=request["rubric_levels"],
            policy_results=request["policy_results"],
            tone_flags=request["tone_flags"],
            transcript_summary=request["transcript_summary"]
        )

        # Initialize evaluator and run
        llm_evaluator = DeterministicLLMEvaluator()
        llm_result, metadata = llm_evaluator.evaluate_recording(evaluation_input)

        # Apply critical rule overrides
        policy_rules = request.get("policy_rules", {})
        final_rubric_levels, overrides_applied = llm_evaluator.apply_critical_overrides(
            llm_result.results,
            evaluation_input.policy_results,
            policy_rules
        )

        # Calculate scores
        scorer = DeterministicScorer()
        rubric_ranges = request.get("rubric_ranges", {})
        category_scores = scorer.calculate_category_scores(
            final_rubric_levels,
            evaluation_input.policy_results,
            rubric_ranges
        )

        # Calculate overall score
        category_weights = request.get("category_weights", {})
        overall_score = scorer.calculate_overall_score(category_scores, category_weights)

        # Store LLM result in evaluation (in production, this would be a separate table)
        evaluation.llm_analysis = {
            "phase4_deterministic": True,
            "llm_result": {
                "evaluation_id": llm_result.evaluation_id,
                "results": final_rubric_levels,
                "llm_meta": llm_result.llm_meta,
                "overrides_applied": overrides_applied,
                "category_scores": category_scores,
                "overall_score": float(overall_score),
                "execution_metadata": metadata
            }
        }

        db.commit()

        logger.info(
            f"Deterministic LLM evaluation completed for {evaluation_id}: "
            f"overall_score={overall_score}, overrides={len(overrides_applied)}"
        )

        return {
            "success": True,
            "evaluation_id": evaluation_id,
            "rubric_levels": final_rubric_levels,
            "category_scores": category_scores,
            "overall_score": float(overall_score),
            "overrides_applied": overrides_applied,
            "llm_meta": llm_result.llm_meta,
            "execution_metadata": metadata
        }

    except Exception as e:
        logger.error(f"Deterministic LLM evaluation failed for {evaluation_id}: {e}")

        # Mark evaluation as requiring human review due to LLM failure
        evaluation.requires_human_review = True
        evaluation.llm_analysis = {
            "phase4_error": str(e),
            "requires_human_review": True
        }
        db.commit()

        raise HTTPException(status_code=500, detail=f"LLM evaluation failed: {str(e)}")


@router.get("/evaluations/{evaluation_id}/llm_result")
async def get_llm_evaluation_result(
    evaluation_id: str,
    current_user: User = Depends(require_internal_access),
    db: Session = Depends(get_db)
):
    """
    Get stored deterministic LLM evaluation result (Phase 4).
    """
    # Validate evaluation exists and user has access
    evaluation = db.query(Evaluation).filter(
        Evaluation.id == evaluation_id,
        Evaluation.company_id == current_user.company_id
    ).first()

    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    llm_analysis = evaluation.llm_analysis or {}

    if "phase4_deterministic" not in llm_analysis:
        raise HTTPException(status_code=404, detail="No deterministic LLM evaluation found")

    return llm_analysis["llm_result"]


@router.post("/evaluations/{evaluation_id}/calculate_scores")
async def calculate_deterministic_scores(
    evaluation_id: str,
    request: dict,
    current_user: User = Depends(require_internal_access),
    db: Session = Depends(get_db)
):
    """
    Calculate deterministic scores from rubric levels and penalties (Phase 4).

    This endpoint can be used independently for score calculation testing.
    """
    logger.info(f"User {current_user.id} calculating deterministic scores for {evaluation_id}")

    # Validate evaluation exists
    evaluation = db.query(Evaluation).filter(
        Evaluation.id == evaluation_id,
        Evaluation.company_id == current_user.company_id
    ).first()

    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    try:
        scorer = DeterministicScorer()

        # Extract inputs
        rubric_levels = request["rubric_levels"]
        policy_results = request["policy_results"]
        rubric_ranges = request.get("rubric_ranges", {})
        category_weights = request.get("category_weights", {})

        # Calculate scores
        category_scores = scorer.calculate_category_scores(rubric_levels, policy_results, rubric_ranges)
        overall_score = scorer.calculate_overall_score(category_scores, category_weights)

        return {
            "success": True,
            "evaluation_id": evaluation_id,
            "category_scores": category_scores,
            "overall_score": float(overall_score)
        }

    except Exception as e:
        logger.error(f"Score calculation failed for {evaluation_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Score calculation failed: {str(e)}")


# Phase 5: Rule Editor UI Endpoints

@router.get("/policy_templates/{template_id}/rules")
async def get_policy_rules_current(
    template_id: str,
    current_user: User = Depends(require_internal_access),
    db: Session = Depends(get_db)
):
    """
    Get current policy rules for a template (Phase 5).

    Returns current published rules, metadata, and editing status.
    """
    template = db.query(PolicyTemplate).filter(
        PolicyTemplate.id == template_id,
        PolicyTemplate.company_id == current_user.company_id
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="Policy template not found")

    # Get latest version
    latest_version = db.query(PolicyRulesVersion).filter(
        PolicyRulesVersion.policy_template_id == template_id
    ).order_by(PolicyRulesVersion.rules_version.desc()).first()

    # Count active drafts
    draft_count = db.query(PolicyRulesDraft).filter(
        PolicyRulesDraft.policy_template_id == template_id,
        PolicyRulesDraft.status.in_([DraftStatus.generating, DraftStatus.needs_clarification,
                                   DraftStatus.ready_for_confirm])
    ).count()

    return {
        "template_id": template_id,
        "current_rules": template.policy_rules,
        "current_version": latest_version.rules_version if latest_version else None,
        "last_published_at": template.published_at.isoformat() if template.published_at else None,
        "last_published_by": template.published_by_user_id,
        "has_active_drafts": draft_count > 0,
        "active_draft_count": draft_count,
        "rules_hash": latest_version.rules_hash if latest_version else None
    }


@router.post("/policy_templates/{template_id}/rules/draft")
async def create_or_update_draft(
    template_id: str,
    request: dict,
    current_user: User = Depends(require_internal_access),
    db: Session = Depends(get_db)
):
    """
    Create or update a draft of policy rules for editing (Phase 5).
    """
    template = db.query(PolicyTemplate).filter(
        PolicyTemplate.id == template_id,
        PolicyTemplate.company_id == current_user.company_id
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="Policy template not found")

    draft_id = request.get("draft_id")
    policy_rules = request.get("policy_rules")
    name = request.get("name")
    description = request.get("description")

    if not policy_rules:
        raise HTTPException(status_code=400, detail="policy_rules is required")

    try:
        # Validate rules
        validator = PolicyRulesValidator()
        normalized_rules = validator.validate_policy_rules({"rules": policy_rules})

        if draft_id:
            # Update existing draft
            draft = db.query(PolicyRulesDraft).filter(
                PolicyRulesDraft.id == draft_id,
                PolicyRulesDraft.policy_template_id == template_id
            ).first()

            if not draft:
                raise HTTPException(status_code=404, detail="Draft not found")

            draft.generated_rules = policy_rules
            draft.is_manual_edit = True
            draft.last_edited_by_user_id = current_user.id

            if name:
                draft.name = name
            if description:
                draft.description = description

            db.commit()

            logger.info(f"Updated draft {draft_id} for template {template_id} by user {current_user.id}")

        else:
            # Create new draft
            parent_version = db.query(PolicyRulesVersion).filter(
                PolicyRulesVersion.policy_template_id == template_id
            ).order_by(PolicyRulesVersion.rules_version.desc()).first()

            draft = PolicyRulesDraft(
                policy_template_id=template_id,
                status=DraftStatus.ready_for_confirm,
                policy_text="",  # Not applicable for manual edits
                generated_rules=policy_rules,
                parent_version=parent_version.rules_version if parent_version else None,
                is_manual_edit=True,
                name=name or f"Manual Edit Draft",
                description=description,
                created_by_user_id=current_user.id,
                last_edited_by_user_id=current_user.id
            )

            db.add(draft)
            db.commit()
            db.refresh(draft)
            draft_id = draft.id

            logger.info(f"Created draft {draft_id} for template {template_id} by user {current_user.id}")

        return {
            "success": True,
            "draft_id": draft_id,
            "message": "Draft saved successfully"
        }

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=f"Rules validation failed: {str(e)}")


@router.post("/policy_templates/{template_id}/rules/drafts/{draft_id}/publish")
async def publish_draft(
    template_id: str,
    draft_id: str,
    request: dict,
    current_user: User = Depends(require_internal_access),
    db: Session = Depends(get_db)
):
    """
    Publish a draft to create a new version and update the template (Phase 5).
    """
    template = db.query(PolicyTemplate).filter(
        PolicyTemplate.id == template_id,
        PolicyTemplate.company_id == current_user.company_id
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="Policy template not found")

    draft = db.query(PolicyRulesDraft).filter(
        PolicyRulesDraft.id == draft_id,
        PolicyRulesDraft.policy_template_id == template_id
    ).first()

    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    if draft.status != DraftStatus.ready_for_confirm:
        raise HTTPException(status_code=400, detail=f"Draft is not ready for publishing (status: {draft.status.value})")

    try:
        # Validate rules one final time
        validator = PolicyRulesValidator()
        normalized_rules = validator.validate_policy_rules({"rules": draft.generated_rules})

        # Create new version
        versioning = PolicyRulesVersioningService()
        version = versioning.create_version(
            policy_template_id=template_id,
            policy_rules=validator.serialize_policy_rules(normalized_rules)["rules"],
            created_by_user_id=current_user.id,
            draft_id=draft_id,
            name=request.get("version_name"),
            notes=request.get("version_notes"),
            llm_generated=False  # Manual edits
        )

        # Update template
        template.policy_rules = version.policy_rules
        template.published_at = version.created_at
        template.published_by_user_id = current_user.id

        # Mark draft as published
        draft.status = DraftStatus.confirmed

        db.commit()

        logger.info(f"Published draft {draft_id} as version {version.rules_version} for template {template_id}")

        return {
            "success": True,
            "version": version.rules_version,
            "rules_hash": version.rules_hash,
            "message": f"Rules published as version {version.rules_version}"
        }

    except ValidationError as e:
        # Mark draft as validation failed
        draft.status = DraftStatus.validation_failed
        draft.validation_errors = [str(e)]
        db.commit()

        raise HTTPException(status_code=400, detail=f"Rules validation failed: {str(e)}")


@router.post("/policy_templates/{template_id}/rules/drafts/{draft_id}/sandbox_evaluate")
async def sandbox_evaluate_draft(
    template_id: str,
    draft_id: str,
    request: dict,
    current_user: User = Depends(require_internal_access),
    db: Session = Depends(get_db)
):
    """
    Run sandbox evaluation of draft rules against sample transcripts (Phase 5).
    """
    template = db.query(PolicyTemplate).filter(
        PolicyTemplate.id == template_id,
        PolicyTemplate.company_id == current_user.company_id
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="Policy template not found")

    draft = db.query(PolicyRulesDraft).filter(
        PolicyRulesDraft.id == draft_id,
        PolicyRulesDraft.policy_template_id == template_id
    ).first()

    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    sample_id = request.get("sample_id")
    custom_transcript = request.get("custom_transcript")

    try:
        sandbox = PolicyRulesSandboxService()
        result = sandbox.evaluate_against_sample(
            policy_rules=draft.generated_rules,
            sample_id=sample_id,
            custom_transcript=custom_transcript
        )

        logger.info(f"Sandbox evaluation completed for draft {draft_id} using sample {result.get('transcript_id')}")

        return result

    except Exception as e:
        logger.error(f"Sandbox evaluation failed for draft {draft_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Sandbox evaluation failed: {str(e)}")


@router.get("/policy_templates/{template_id}/rules/samples")
async def get_sandbox_samples(
    template_id: str,
    current_user: User = Depends(require_internal_access),
    db: Session = Depends(get_db)
):
    """
    Get available sample transcripts for sandbox evaluation (Phase 5).
    """
    template = db.query(PolicyTemplate).filter(
        PolicyTemplate.id == template_id,
        PolicyTemplate.company_id == current_user.company_id
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="Policy template not found")

    sandbox = PolicyRulesSandboxService()
    samples = sandbox.get_available_samples()

    return {
        "template_id": template_id,
        "samples": samples
    }


@router.get("/policy_templates/{template_id}/rules/history")
async def get_rules_history(
    template_id: str,
    limit: int = 20,
    current_user: User = Depends(require_internal_access),
    db: Session = Depends(get_db)
):
    """
    Get version history for policy rules (Phase 5).
    """
    template = db.query(PolicyTemplate).filter(
        PolicyTemplate.id == template_id,
        PolicyTemplate.company_id == current_user.company_id
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="Policy template not found")

    versioning = PolicyRulesVersioningService()
    history = versioning.get_version_history(template_id, limit=limit)

    return {
        "template_id": template_id,
        "history": history
    }


@router.post("/policy_templates/{template_id}/rules/{version}/rollback")
async def rollback_to_version(
    template_id: str,
    version: int,
    request: dict,
    current_user: User = Depends(require_internal_access),
    db: Session = Depends(get_db)
):
    """
    Rollback to a previous version of policy rules (Phase 5).
    """
    template = db.query(PolicyTemplate).filter(
        PolicyTemplate.id == template_id,
        PolicyTemplate.company_id == current_user.company_id
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="Policy template not found")

    notes = request.get("notes")

    try:
        versioning = PolicyRulesVersioningService()
        target_version, new_version = versioning.rollback_to_version(
            policy_template_id=template_id,
            target_version=version,
            rollback_by_user_id=current_user.id,
            notes=notes
        )

        logger.info(f"Rolled back template {template_id} to version {version} (new version {new_version.rules_version})")

        return {
            "success": True,
            "rolled_back_to": version,
            "new_version": new_version.rules_version,
            "rules_hash": new_version.rules_hash,
            "message": f"Successfully rolled back to version {version}"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Rollback failed for template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Rollback failed: {str(e)}")


@router.post("/policy_templates/{template_id}/rules/versions/{version}/create_draft")
async def create_draft_from_version(
    template_id: str,
    version: int,
    request: dict,
    current_user: User = Depends(require_internal_access),
    db: Session = Depends(get_db)
):
    """
    Create a draft from an existing version for editing (Phase 5).
    """
    template = db.query(PolicyTemplate).filter(
        PolicyTemplate.id == template_id,
        PolicyTemplate.company_id == current_user.company_id
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="Policy template not found")

    draft_name = request.get("name")
    draft_description = request.get("description")

    try:
        versioning = PolicyRulesVersioningService()
        draft = versioning.create_draft_from_version(
            policy_template_id=template_id,
            version_number=version,
            created_by_user_id=current_user.id,
            draft_name=draft_name,
            draft_description=draft_description
        )

        logger.info(f"Created draft {draft.id} from version {version} of template {template_id}")

        return {
            "success": True,
            "draft_id": draft.id,
            "version_used": version,
            "message": "Draft created from version"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Create draft from version failed for template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Create draft failed: {str(e)}")


@router.get("/policy_rules/schema")
async def get_policy_rules_schema(
    current_user: User = Depends(require_internal_access)
):
    """
    Get the JSON schema for policy rules validation (Phase 5).

    Used by frontend to generate forms and validate inputs.
    """
    validator = PolicyRulesValidator()
    schema = validator.get_schema()

    return {
        "schema": schema,
        "supported_rule_types": ["boolean", "numeric", "list"],
        "supported_comparators": ["le", "lt", "eq", "ge", "gt"],
        "max_payload_size_kb": 50
    }
