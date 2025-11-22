"""
Phase 7: Final Evaluation Pipeline
Implements the standardized Phase 7 pipeline per spec.
"""

from app.database import SessionLocal
from app.models.recording import Recording, RecordingStatus
from app.models.transcript import Transcript
from app.models.evaluation import Evaluation, EvaluationStatus
from app.models.flow_version import FlowVersion
from app.models.compliance_rule import ComplianceRule
from app.models.rubric_template import RubricTemplate
from app.services.deepgram import DeepgramService
from app.services.transcript_normalizer import TranscriptNormalizer
from app.services.deterministic_rule_engine import DeterministicRuleEngine
from app.services.llm_stage_evaluator import LLMStageEvaluator
from app.services.rubric_scorer import RubricScorer
from app.services.email import EmailService
from app.services.audit import AuditService
from app.models.audit import AuditEventType
from app.models.human_review import HumanReview, ReviewStatus
from datetime import datetime
import logging
import json
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


async def process_recording_phase7(recording_id: str):
    """
    Phase 7: Final Evaluation Pipeline
    Implements the standardized pipeline: Transcription → Deterministic → LLM (per stage) → Rubric Scoring → Final Evaluation
    """
    db = SessionLocal()
    try:
        # STEP 1: Get recording
        recording = db.query(Recording).filter(Recording.id == recording_id).first()
        if not recording:
            logger.error(f"Recording {recording_id} not found")
            return
        
        # Update status
        recording.status = RecordingStatus.processing
        db.commit()
        
        # STEP 2: Transcription
        logger.info(f"Phase 7: Transcribing {recording_id}...")
        deepgram = DeepgramService()
        transcript_data = await deepgram.transcribe(recording.file_url)
        
        # Transcript normalization
        normalizer = TranscriptNormalizer()
        normalized_text, processed_segments, normalization_metadata = normalizer.normalize_transcript(
            raw_transcript=transcript_data["transcript"],
            diarized_segments=transcript_data["diarized_segments"] or []
        )
        
        # Save transcript
        transcript = Transcript(
            recording_id=recording_id,
            transcript_text=normalized_text,
            diarized_segments=processed_segments,
            sentiment_analysis=transcript_data.get("sentiment_analysis"),
            transcription_confidence=float(transcript_data["confidence"]) if transcript_data.get("confidence") else None,
            deepgram_confidence=float(transcript_data["confidence"]) if transcript_data.get("confidence") else None,
            normalized_text=normalized_text
        )
        db.add(transcript)
        db.commit()
        
        # STEP 3: Load Active Policy Components
        logger.info(f"Phase 7: Loading FlowVersion and policy components...")
        
        # Get active FlowVersion for company
        flow_version = db.query(FlowVersion).filter(
            FlowVersion.company_id == recording.company_id,
            FlowVersion.is_active == True
        ).order_by(FlowVersion.created_at.desc()).first()
        
        if not flow_version:
            raise Exception(f"No active FlowVersion found for company {recording.company_id}")
        
        # Get ComplianceRules for FlowVersion
        compliance_rules = db.query(ComplianceRule).filter(
            ComplianceRule.flow_version_id == flow_version.id,
            ComplianceRule.active == True
        ).all()
        
        # Get RubricTemplate for FlowVersion
        rubric_template = db.query(RubricTemplate).filter(
            RubricTemplate.flow_version_id == flow_version.id,
            RubricTemplate.is_active == True
        ).first()
        
        if not rubric_template:
            raise Exception(f"No active RubricTemplate found for FlowVersion {flow_version.id}")
        
        # STEP 4: Deterministic Rule Engine (Phase 3)
        logger.info(f"Phase 7: Running Deterministic Rule Engine...")
        deterministic_engine = DeterministicRuleEngine()
        
        deterministic_result = deterministic_engine.evaluate(
            flow_version=flow_version,
            compliance_rules=compliance_rules,
            transcript_text=normalized_text,
            segments=processed_segments
        )
        
        # Add metadata
        deterministic_result["evaluation_id"] = f"eval_{recording_id}"
        deterministic_result["flow_version_id"] = flow_version.id
        deterministic_result["recording_id"] = recording_id
        
        # STEP 5: LLM Stage Evaluation (Phase 4) - per stage
        logger.info(f"Phase 7: Running LLM Stage Evaluator for {len(flow_version.stages)} stages...")
        llm_evaluator = LLMStageEvaluator()
        llm_stage_evaluations = {}
        
        # Get evaluation config (defaults)
        evaluation_config = {
            "penalty_missing_required": 20,
            "penalty_major": 40,
            "penalty_minor": 10,
            "penalty_timing": 10,
            "discretionary_max": 10
        }
        
        # Evaluate each stage
        for stage in sorted(flow_version.stages, key=lambda s: s.order):
            # Get segments for this stage (simplified - would need stage boundary detection)
            # For now, use all segments (stage boundaries would be detected from step timestamps)
            stage_segments = processed_segments  # TODO: Implement stage boundary detection
            
            # Get rubric mapping hint (simplified)
            rubric_mapping = None  # TODO: Get from RubricTemplate mappings
            
            try:
                stage_eval = llm_evaluator.evaluate_stage(
                    stage_id=stage.id,
                    stage_segments=stage_segments,
                    deterministic_results=deterministic_result,
                    flow_version=flow_version,
                    rubric_mapping=rubric_mapping,
                    evaluation_config=evaluation_config,
                    evaluation_id=deterministic_result["evaluation_id"],
                    recording_id=recording_id
                )
                llm_stage_evaluations[stage.id] = stage_eval
            except Exception as e:
                logger.error(f"LLM evaluation failed for stage {stage.id}: {e}", exc_info=True)
                # Use deterministic fallback
                stage_eval = llm_evaluator._create_deterministic_fallback(
                    stage.id,
                    deterministic_result,
                    f"LLM evaluation error: {str(e)}"
                )
                llm_stage_evaluations[stage.id] = stage_eval
        
        # STEP 6: Combine LLM stage evaluations (already done above)
        
        # STEP 7: Rubric Scoring Engine (Phase 6)
        logger.info(f"Phase 7: Running Rubric Scorer...")
        rubric_scorer = RubricScorer()
        
        final_evaluation = rubric_scorer.score(
            rubric_template=rubric_template,
            llm_stage_evaluations=llm_stage_evaluations,
            deterministic_result=deterministic_result
        )
        
        # STEP 8: Final Evaluation Assembly
        logger.info(f"Phase 7: Assembling final evaluation...")
        
        # Create Evaluation record
        evaluation = Evaluation(
            recording_id=recording_id,
            evaluated_by_user_id=recording.uploaded_by_user_id,
            overall_score=final_evaluation["overall_score"],
            resolution_detected=False,  # TODO: Extract from LLM evaluations
            resolution_confidence=0.0,
            confidence_score=min(s.get("stage_confidence", 0.5) for s in llm_stage_evaluations.values()) if llm_stage_evaluations else 0.5,
            requires_human_review=final_evaluation.get("requires_human_review", False),
            customer_tone=None,
            llm_analysis=llm_stage_evaluations,
            status=EvaluationStatus.completed,
            # Store Phase 7 data
            deterministic_results=deterministic_result,
            llm_stage_evaluations=llm_stage_evaluations,
            final_evaluation=final_evaluation,
            flow_version_id=flow_version.id,
            rubric_template_id=rubric_template.id,
            # Metadata
            prompt_version="phase7",
            model_version="gemini-2.5-flash",
            model_temperature=0.0,
            model_top_p=0.95
        )
        db.add(evaluation)
        db.flush()
        
        # Save category scores (from final_evaluation)
        from app.models.category_score import CategoryScore
        for cat_score_data in final_evaluation.get("category_scores", []):
            cat_score = CategoryScore(
                evaluation_id=evaluation.id,
                category_name=cat_score_data["name"],
                score=cat_score_data["score"],
                feedback=f"Category: {cat_score_data['name']}, Passed: {cat_score_data['passed']}"
            )
            db.add(cat_score)
        
        # Violations are already stored in evaluation.deterministic_results["rule_violations"]
        # Legacy PolicyViolation table removed - no need to create separate violation records
        violations_saved = len(deterministic_result.get("rule_violations", []))
        logger.info(f"Violations stored in deterministic_results: {violations_saved} violations")
        
        # Create human review if needed
        if final_evaluation.get("requires_human_review", False):
            logger.info(f"Low confidence - creating human review request")
            human_review = HumanReview(
                recording_id=recording_id,
                evaluation_id=evaluation.id,
                reviewer_user_id=None,
                review_status=ReviewStatus.pending,
                ai_score_accuracy=None,
                human_overall_score=None,
                human_category_scores=None
            )
            db.add(human_review)
        
        # Audit logging
        try:
            audit_service = AuditService()
            audit_service.log_evaluation_event(
                event_type=AuditEventType.evaluation_created,
                evaluation_id=evaluation.id,
                user_id=recording.uploaded_by_user_id,
                new_values={
                    "overall_score": final_evaluation["overall_score"],
                    "overall_passed": final_evaluation["overall_passed"],
                    "flow_version_id": flow_version.id,
                    "rubric_template_id": rubric_template.id
                },
                description=f"Phase 7 evaluation completed for recording {recording.file_name}",
                reason="Standardized Phase 7 pipeline",
                model_version="phase7",
                confidence_score=evaluation.confidence_score
            )
        except Exception as audit_error:
            logger.warning(f"Audit logging failed: {audit_error}")
        
        db.commit()
        
        # STEP 9: Mark Recording as Completed
        recording.status = RecordingStatus.completed
        recording.processed_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Phase 7: Recording {recording_id} processed successfully")
        
        # Send notification
        try:
            from app.models.user import User
            user = db.query(User).filter(User.id == recording.uploaded_by_user_id).first()
            if user and user.email:
                email_service = EmailService()
                email_service.send_processing_complete_notification(
                    to_email=user.email,
                    recording_name=recording.file_name,
                    score=final_evaluation["overall_score"]
                )
        except Exception as e:
            logger.error(f"Failed to send notification: {str(e)}")
        
    except Exception as e:
        logger.error(f"Error processing recording {recording_id} with Phase 7: {str(e)}", exc_info=True)
        try:
            db.rollback()
            if recording:
                db.refresh(recording)
                recording.status = RecordingStatus.failed
                recording.error_message = str(e)[:500]
                db.commit()
        except Exception as commit_error:
            logger.error(f"Error updating recording status to failed: {commit_error}", exc_info=True)
        
        # Send failure notification
        try:
            from app.models.user import User
            user = db.query(User).filter(User.id == recording.uploaded_by_user_id).first()
            if user and user.email:
                email_service = EmailService()
                email_service.send_processing_failed_notification(
                    to_email=user.email,
                    recording_name=recording.file_name if recording else "Unknown",
                    error_message=str(e)
                )
        except Exception as notification_error:
            logger.error(f"Failed to send failure notification: {str(notification_error)}")
    
    finally:
        db.close()

