"""
Phase 2: Policy Rule Builder - Async Job Worker
Handles background processing of policy rule generation from human-written text.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.policy_rules_draft import PolicyRulesDraft, DraftStatus
from app.services.policy_rule_builder import PolicyRuleBuilder
from app.config import settings

logger = logging.getLogger(__name__)


class GeneratePolicyRulesJob:
    """
    Async job worker for generating policy rules from human-written text.

    Handles the complete lifecycle:
    1. LLM rule generation
    2. Response parsing and validation
    3. Clarification handling
    4. Draft status management
    """

    def __init__(self):
        self.policy_builder = PolicyRuleBuilder()
        self.max_retries = 3
        self.retry_delays = [1, 3, 10]  # seconds

    async def execute(self, draft_id: str) -> Dict[str, Any]:
        """
        Execute the policy rule generation job.

        Args:
            draft_id: ID of the policy rules draft to process

        Returns:
            Job result metadata
        """
        logger.info(f"Starting policy rules generation job for draft {draft_id}")

        db = SessionLocal()
        try:
            # Load draft
            draft = db.query(PolicyRulesDraft).filter(PolicyRulesDraft.id == draft_id).first()
            if not draft:
                raise ValueError(f"Draft {draft_id} not found")

            # Update status to generating
            draft.status = DraftStatus.generating
            db.commit()

            # Execute generation with retries
            result = await self._execute_with_retries(draft, db)

            logger.info(
                f"Policy rules generation completed for draft {draft_id}: status={result.get('status')}, "
                f"rules_count={result.get('rules_count', 0)}, categories={len(result.get('categories', []))}"
            )
            return result

        except Exception as e:
            logger.error(f"Policy rules generation failed for draft {draft_id}: {e}")

            # Update draft status to failed
            if draft:
                draft.status = DraftStatus.failed
                draft.llm_raw_response = str(e)
                db.commit()

            raise
        finally:
            db.close()

    async def _execute_with_retries(self, draft: PolicyRulesDraft, db: Session) -> Dict[str, Any]:
        """
        Execute rule generation with retry logic and error handling.
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                logger.info(f"Attempt {attempt + 1}/{self.max_retries} for draft {draft.id}")

                # Call LLM to generate rules
                llm_response, metadata = self.policy_builder.generate_policy_rules(
                    policy_text=draft.policy_text,
                    rubric_levels=draft.rubric_levels,
                    examples=draft.examples,
                    user_answers=draft.user_answers
                )

                # Update draft with LLM metadata
                draft.llm_model = metadata["llm_model"]
                draft.llm_tokens_used = metadata["llm_tokens_used"]
                draft.llm_latency_ms = metadata["llm_latency_ms"]
                draft.llm_prompt_hash = metadata["llm_prompt_hash"]
                draft.llm_raw_response = metadata["raw_response"]

                # Process the LLM response
                return await self._process_llm_response(draft, llm_response, metadata, db)

            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1} failed for draft {draft.id}: {e}")

                # If not the last attempt, wait before retry
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delays[attempt])

                continue

        # All retries failed
        raise last_error or Exception("All retry attempts failed")

    async def _process_llm_response(
        self,
        draft: PolicyRulesDraft,
        llm_response: Dict[str, Any],
        metadata: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """
        Process the LLM response and update draft accordingly.
        """
        policy_rules = llm_response.get("policy_rules", {})
        clarifications = llm_response.get("clarifications", [])

        # Store generated rules
        draft.generated_rules = policy_rules
        draft.clarifications = clarifications

        # Check if clarifications are needed
        if clarifications and len(clarifications) > 0:
            # Draft needs clarification from user
            draft.status = DraftStatus.needs_clarification
            db.commit()

            return {
                "status": "needs_clarification",
                "clarifications_count": len(clarifications),
                "clarifications": clarifications
            }

        # No clarifications needed - validate the generated rules
        is_valid, normalized_rules, validation_errors = self.policy_builder.validate_generated_rules(policy_rules)

        if not is_valid:
            # Validation failed
            draft.status = DraftStatus.validation_failed
            draft.validation_errors = validation_errors
            db.commit()

            return {
                "status": "validation_failed",
                "errors": validation_errors
            }

        # Rules are valid and ready for confirmation
        draft.status = DraftStatus.ready_for_confirm
        db.commit()

        return {
            "status": "ready_for_confirm",
            "rules_count": sum(len(rules) for rules in policy_rules.values()),
            "categories": list(policy_rules.keys())
        }

    async def clarify_and_regenerate(self, draft_id: str, user_answers: Dict[str, str]) -> Dict[str, Any]:
        """
        Handle clarification answers and regenerate rules.

        Args:
            draft_id: ID of the draft to clarify
            user_answers: User's answers to clarification questions

        Returns:
            Job result metadata
        """
        logger.info(f"Processing clarification for draft {draft_id}")

        db = SessionLocal()
        try:
            # Load draft
            draft = db.query(PolicyRulesDraft).filter(PolicyRulesDraft.id == draft_id).first()
            if not draft:
                raise ValueError(f"Draft {draft_id} not found")

            if draft.status != DraftStatus.needs_clarification:
                raise ValueError(f"Draft {draft_id} is not in needs_clarification status")

            # Store user answers
            draft.user_answers = user_answers
            draft.status = DraftStatus.generating
            db.commit()

            # Regenerate with answers
            result = await self._execute_with_retries(draft, db)

            return result

        except Exception as e:
            logger.error(f"Clarification processing failed for draft {draft_id}: {e}")
            raise
        finally:
            db.close()

    def get_draft_status(self, draft_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current status of a draft.

        Args:
            draft_id: ID of the draft to check

        Returns:
            Draft status information or None if not found
        """
        db = SessionLocal()
        try:
            draft = db.query(PolicyRulesDraft).filter(PolicyRulesDraft.id == draft_id).first()
            if not draft:
                return None

            return {
                "id": draft.id,
                "status": draft.status.value,
                "created_at": draft.created_at.isoformat(),
                "updated_at": draft.updated_at.isoformat(),
                "llm_model": draft.llm_model,
                "llm_tokens_used": draft.llm_tokens_used,
                "llm_latency_ms": draft.llm_latency_ms,
                "generated_rules": draft.generated_rules,
                "clarifications": draft.clarifications,
                "validation_errors": draft.validation_errors
            }

        finally:
            db.close()


# Global job instance for use by task queue
policy_rules_job = GeneratePolicyRulesJob()


async def generate_policy_rules_task(draft_id: str) -> Dict[str, Any]:
    """
    Task function for the job queue system.
    """
    return await policy_rules_job.execute(draft_id)


async def clarify_policy_rules_task(draft_id: str, user_answers: Dict[str, str]) -> Dict[str, Any]:
    """
    Task function for clarification processing.
    """
    return await policy_rules_job.clarify_and_regenerate(draft_id, user_answers)
