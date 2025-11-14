from app.database import SessionLocal
from app.models.recording import Recording, RecordingStatus
from app.models.transcript import Transcript
from app.models.evaluation import Evaluation, EvaluationStatus
from app.models.category_score import CategoryScore
from app.models.policy_violation import PolicyViolation
from app.models.evaluation_criteria import EvaluationCriteria
from app.services.deepgram import DeepgramService
from app.services.gemini import GeminiService
from app.services.scoring import ScoringService
from app.services.email import EmailService
from app.services.confidence import ConfidenceService  # Phase 1: Confidence-based routing
from app.services.rule_engine import RuleEngineService  # Phase 2: Rule engine
from app.services.audit import AuditService  # Phase 4: Compliance & audit
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


async def process_recording_task(recording_id: str):
    """Background task to process recording"""
    db = SessionLocal()
    try:
        # Get recording
        recording = db.query(Recording).filter(Recording.id == recording_id).first()
        if not recording:
            logger.error(f"Recording {recording_id} not found")
            return
        
        # Update status
        recording.status = RecordingStatus.processing
        db.commit()
        
        # Step 1: Transcribe
        logger.info(f"Transcribing {recording_id}...")
        deepgram = DeepgramService()
        transcript_data = await deepgram.transcribe(recording.file_url)
        
        # Save transcript
        transcript = Transcript(
            recording_id=recording_id,
            transcript_text=transcript_data["transcript"],
            diarized_segments=transcript_data["diarized_segments"],
            sentiment_analysis=transcript_data.get("sentiment_analysis"),  # Voice-based sentiment
            transcription_confidence=float(transcript_data["confidence"]) if transcript_data.get("confidence") else None,
            # MVP Evaluation Improvements: Store Deepgram confidence
            deepgram_confidence=float(transcript_data["confidence"]) if transcript_data.get("confidence") else None
        )
        db.add(transcript)
        db.commit()
        
        # Step 2: Get policy template
        # Note: In production, policy_template_id should be passed during upload
        # For now, use the first active template for the company
        from app.models.policy_template import PolicyTemplate
        policy_template = db.query(PolicyTemplate).filter(
            PolicyTemplate.company_id == recording.company_id,
            PolicyTemplate.is_active == True
        ).first()
        
        if not policy_template:
            raise Exception(f"No active policy template found for company {recording.company_id}")
        
        # Step 3: Phase 2 - Run rule engine for explicit policy compliance checking
        sentiment_data = transcript.sentiment_analysis
        if isinstance(sentiment_data, str):
            # If it's stored as a string, try to parse it as JSON
            import json
            try:
                sentiment_data = json.loads(sentiment_data)
                logger.warning(f"Parsed sentiment_analysis from string: {type(sentiment_data)}")
            except json.JSONDecodeError:
                logger.error(f"Failed to parse sentiment_analysis string: {sentiment_data[:100]}...")
                sentiment_data = []
        elif sentiment_data is None:
            sentiment_data = []

        logger.info(f"Passing sentiment_analysis to rule engine: type={type(sentiment_data)}, len={len(sentiment_data) if isinstance(sentiment_data, list) else 'N/A'}")

        rule_engine = RuleEngineService()
        rule_results = rule_engine.evaluate_rules(
            transcript_segments=transcript.diarized_segments or [],
            sentiment_analysis=sentiment_data
        )

        # Step 4: Evaluate with LLM (with rule engine context)
        logger.info(f"Evaluating {recording_id}...")
        gemini = GeminiService()
        # Pass voice-based sentiment analysis (BOTH caller and agent) to LLM for tone detection
        # This enables detection of tone mismatches and disingenuous behavior
        sentiment_analysis_for_gemini = transcript.sentiment_analysis
        if isinstance(sentiment_analysis_for_gemini, str):
            # If it's stored as a string, try to parse it as JSON
            import json
            try:
                sentiment_analysis_for_gemini = json.loads(sentiment_analysis_for_gemini)
                logger.info(f"Parsed sentiment_analysis for Gemini: {type(sentiment_analysis_for_gemini)} len: {len(sentiment_analysis_for_gemini)}")
            except json.JSONDecodeError:
                logger.error(f"Failed to parse sentiment_analysis for Gemini: {sentiment_analysis_for_gemini[:100]}...")
                sentiment_analysis_for_gemini = None
        elif sentiment_analysis_for_gemini is None:
            sentiment_analysis_for_gemini = None

        evaluation_result = await gemini.evaluate(
            transcript_text=transcript.transcript_text,
            policy_template_id=policy_template.id,
            sentiment_analysis=sentiment_analysis_for_gemini,
            rule_results=rule_results  # Phase 2: Include rule engine results
        )

        # MVP Evaluation Improvements: Extract evaluation data and raw response
        evaluation_data = evaluation_result["evaluation"]
        raw_llm_response = evaluation_result["raw_llm_response"]

        # Validate evaluation data
        if not evaluation_data or not isinstance(evaluation_data, dict):
            raise Exception("Invalid evaluation data returned from LLM")
        
        if "category_scores" not in evaluation_data:
            raise Exception("Evaluation data missing required 'category_scores' field")
        
        # Step 4: Get criteria for scoring (with rubric levels)
        from sqlalchemy.orm import joinedload
        criteria = db.query(EvaluationCriteria).options(
            joinedload(EvaluationCriteria.rubric_levels)
        ).filter(
            EvaluationCriteria.policy_template_id == policy_template.id
        ).all()
        
        # Step 5: Calculate individual scores first
        scoring = ScoringService()
        llm_scores = scoring.calculate_scores(evaluation_data, criteria)

        # Step 5.5: Phase 2 - Ensemble evaluation combining LLM + Rules (+ Emotion when available)
        # For now, we combine LLM scores with rule engine scores
        # Emotion classifier will be added later
        final_scores = scoring.calculate_ensemble_scores(
            llm_scores=llm_scores,
            rule_scores=rule_results.get("rule_scores"),
            emotion_deviation_scores=None,  # TODO: Add emotion classifier in Phase 2
            criteria=criteria
        )

        # Validate final scores
        if not final_scores or not isinstance(final_scores, dict):
            raise Exception("Invalid final scores returned from scoring service")
        
        required_score_fields = ["overall_score", "resolution_detected", "resolution_confidence", "category_scores"]
        missing_fields = [field for field in required_score_fields if field not in final_scores]
        if missing_fields:
            raise Exception(f"Final scores missing required fields: {missing_fields}")

        # Step 5.5: Phase 1 - Calculate confidence for human fallback routing
        confidence_service = ConfidenceService()
        confidence_result = confidence_service.calculate_overall_confidence(
            llm_evaluation=evaluation_data,
            sentiment_analysis=transcript.sentiment_analysis
        )

        # Validate confidence result
        if not confidence_result or not isinstance(confidence_result, dict):
            raise Exception("Invalid confidence result returned from confidence service")
        
        if "confidence_score" not in confidence_result or "requires_human_review" not in confidence_result:
            raise Exception("Confidence result missing required fields: confidence_score or requires_human_review")

        # Step 6: Save evaluation
        # Extract customer tone from evaluation data
        customer_tone = evaluation_data.get("customer_tone")
        
        # MVP Evaluation Improvements: Set reproducibility metadata
        model_name = raw_llm_response.get("model", "unknown")
        prompt_text = raw_llm_response.get("prompt", "")
        generation_config = raw_llm_response.get("generation_config", {})

        evaluation = Evaluation(
            recording_id=recording_id,
            policy_template_id=policy_template.id,
            evaluated_by_user_id=recording.uploaded_by_user_id,
            overall_score=final_scores["overall_score"],
            resolution_detected=final_scores["resolution_detected"],
            resolution_confidence=final_scores["resolution_confidence"],
            confidence_score=confidence_result["confidence_score"],  # Phase 1: AI confidence score
            requires_human_review=confidence_result["requires_human_review"],  # Phase 1: Human routing flag
            customer_tone=customer_tone,
            llm_analysis=evaluation_data,
            status=EvaluationStatus.completed,
            # MVP Evaluation Improvements: Reproducibility metadata
            prompt_id=f"eval_{policy_template.id}_{recording_id}",  # Generate deterministic prompt ID
            prompt_version="1.0",  # Version for prompt template
            model_version=model_name,
            model_temperature=generation_config.get("temperature", 0.0),
            model_top_p=generation_config.get("top_p", 1.0),
            llm_raw=raw_llm_response,  # Store full raw response
            rubric_version="1.0",  # Version for rubric system
            evaluation_seed=recording_id  # Use recording ID as deterministic seed
        )
        db.add(evaluation)
        db.flush()
        
        # Step 7: Save category scores
        # Only save scores for categories that exist in the criteria (double-check)
        valid_category_names = {c.category_name for c in criteria}
        for category_name, score_data in final_scores["category_scores"].items():
            # Verify category exists in criteria (should be filtered already, but double-check)
            if category_name not in valid_category_names:
                logger.warning(f"Skipping category score for '{category_name}' - not in criteria list")
                continue
                
            cat_score = CategoryScore(
                evaluation_id=evaluation.id,
                category_name=category_name,
                score=score_data["score"],
                feedback=score_data.get("feedback", "")
            )
            db.add(cat_score)
        
        # Step 8: Save violations
        # Create a mapping from category names to criteria IDs (case-insensitive matching)
        category_to_criteria = {}
        for c in criteria:
            # Store both exact and lowercase versions for flexible matching
            category_to_criteria[c.category_name] = c.id
            category_to_criteria[c.category_name.lower()] = c.id
        
        violations_saved = 0
        for violation in final_scores.get("violations", []):
            # Get category name from violation (preferred) or try to infer from type
            category_name = violation.get("category_name") or violation.get("type", "")
            criteria_id = violation.get("criteria_id")
            
            # If criteria_id is provided, validate it's a real UUID
            if criteria_id:
                # Check if it looks like a UUID (36 chars with hyphens, or 32 without)
                is_uuid_like = (len(criteria_id) == 36 and criteria_id.count("-") == 4) or \
                              (len(criteria_id) == 32 and criteria_id.replace("-", "").isalnum())
                if not is_uuid_like:
                    # Not a valid UUID, ignore it and try to match by category name
                    criteria_id = None
                else:
                    # Validate the criteria_id exists in our criteria list
                    if criteria_id not in [c.id for c in criteria]:
                        logger.warning(f"Criteria ID {criteria_id} from LLM not found in database criteria, trying category name match")
                        criteria_id = None
            
            # Try to find criteria by category name (exact match first, then case-insensitive)
            if not criteria_id and category_name:
                criteria_id = category_to_criteria.get(category_name) or category_to_criteria.get(category_name.lower())
                
                # Try partial match if exact match fails
                if not criteria_id:
                    for criterion in criteria:
                        cat_lower = criterion.category_name.lower()
                        violation_lower = category_name.lower()
                        # Check if category name contains violation type or vice versa
                        if violation_lower in cat_lower or cat_lower in violation_lower:
                            criteria_id = criterion.id
                            logger.info(f"Matched violation category '{category_name}' to criteria '{criterion.category_name}' (ID: {criteria_id})")
                            break
            
            # If we still can't find a matching criteria, log and skip this violation
            if not criteria_id:
                logger.warning(f"Could not find matching criteria for violation: type='{violation.get('type')}', category='{category_name}', description='{violation.get('description', '')[:50]}...'")
                logger.warning(f"Available categories: {[c.category_name for c in criteria]}")
                continue
            
            # Validate severity
            severity = violation.get("severity", "minor")
            if severity not in ["critical", "major", "minor"]:
                severity = "minor"
            
            try:
                policy_viol = PolicyViolation(
                    evaluation_id=evaluation.id,
                    criteria_id=criteria_id,
                    violation_type=violation.get("type", "unknown"),
                    description=violation.get("description", ""),
                    severity=severity
                )
                db.add(policy_viol)
                violations_saved += 1
                logger.info(f"Saved violation: {violation.get('type')} (criteria_id: {criteria_id}, severity: {severity})")
            except Exception as e:
                logger.error(f"Error saving violation: {e}", exc_info=True)
                # Continue with other violations even if one fails
                continue
        
        logger.info(f"Saved {violations_saved} violations out of {len(final_scores.get('violations', []))} total")

        # Step 9: Phase 1 - Human Review Routing
        if confidence_result["requires_human_review"]:
            logger.info(f"Low confidence ({confidence_result['confidence_score']:.2f}) - creating human review request: {confidence_result['reason']}")

            from app.models.human_review import HumanReview, ReviewStatus
            human_review = HumanReview(
                evaluation_id=evaluation.id,
                reviewer_user_id=None,  # Will be assigned when picked up
                review_status=ReviewStatus.pending,
                ai_score_accuracy=None,  # To be filled by human
                human_overall_score=None,
                human_category_scores=None
            )
            db.add(human_review)
            db.commit()

            logger.info(f"Created human review {human_review.id} for evaluation {evaluation.id}")

        try:
            db.commit()
        except Exception as commit_error:
            logger.error(f"Error committing evaluation data: {commit_error}", exc_info=True)
            db.rollback()
            raise
        
        # Step 10: Phase 4 - Create audit trail and evaluation version
        audit_service = AuditService()
        try:
            # Create audit log for evaluation completion
            audit_service.log_evaluation_event(
                event_type=AuditEventType.evaluation_created,
                evaluation_id=evaluation.id,
                user_id=recording.uploaded_by_user_id,
                new_values={
                    "overall_score": final_scores["overall_score"],
                    "confidence_score": confidence_result["confidence_score"],
                    "requires_human_review": confidence_result["requires_human_review"],
                    "llm_analysis": evaluation.llm_analysis,
                    "model_used": evaluation.llm_analysis.get("model_used", "unknown") if evaluation.llm_analysis else "unknown",
                    "complexity_score": evaluation.llm_analysis.get("complexity_score", 0) if evaluation.llm_analysis else 0
                },
                description=f"AI evaluation completed for recording {recording.file_name}",
                reason="Automated QA evaluation pipeline",
                model_version=evaluation.llm_analysis.get("model_used", "unknown") if evaluation.llm_analysis else "unknown",
                confidence_score=confidence_result["confidence_score"]
            )

            # Create evaluation version snapshot for audit trail
            audit_service.create_evaluation_version(
                evaluation_id=evaluation.id,
                created_by="system",  # Automated processing
                change_reason="Initial AI evaluation"
            )

        except Exception as audit_error:
            logger.warning(f"Audit logging failed: {audit_error}")

        # Step 11: Update recording status
        recording.status = RecordingStatus.completed
        recording.processed_at = datetime.utcnow()
        try:
            db.commit()
        except Exception as commit_error:
            logger.error(f"Error updating recording status: {commit_error}", exc_info=True)
            db.rollback()
            raise
        
        logger.info(f"Recording {recording_id} processed successfully")

        # Step 12: Send notification (optional)
        try:
            from app.models.user import User
            user = db.query(User).filter(User.id == recording.uploaded_by_user_id).first()
            if user and user.email:
                email_service = EmailService()
                email_service.send_processing_complete_notification(
                    to_email=user.email,
                    recording_name=recording.file_name,
                    score=final_scores["overall_score"]
                )
        except Exception as e:
            logger.error(f"Failed to send notification: {str(e)}")
        
    except Exception as e:
        logger.error(f"Error processing recording {recording_id}: {str(e)}", exc_info=True)
        try:
            # Rollback any pending transaction first
            db.rollback()
            # Refresh recording to get current state
            db.refresh(recording)
            recording.status = RecordingStatus.failed
            recording.error_message = str(e)[:500]  # Limit error message length
            db.commit()
        except Exception as commit_error:
            logger.error(f"Error updating recording status to failed: {commit_error}", exc_info=True)
            try:
                db.rollback()
            except:
                pass
        
        # Send failure notification
        try:
            from app.models.user import User
            user = db.query(User).filter(User.id == recording.uploaded_by_user_id).first()
            if user and user.email:
                email_service = EmailService()
                email_service.send_processing_failed_notification(
                    to_email=user.email,
                    recording_name=recording.file_name,
                    error_message=str(e)
                )
        except Exception as notification_error:
            logger.error(f"Failed to send failure notification: {str(notification_error)}")
    
    finally:
        db.close()

