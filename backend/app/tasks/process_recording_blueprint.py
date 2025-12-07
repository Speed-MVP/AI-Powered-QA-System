"""
Process Recording Blueprint Task - Phase 9
Cloud Tasks handler for recording evaluation using Blueprint system
"""

import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.recording import Recording, RecordingStatus
from app.models.evaluation import Evaluation, EvaluationStatus
from app.models.transcript import Transcript
from app.models.qa_blueprint import QABlueprint, BlueprintStatus
from app.services.evaluation_pipeline import EvaluationPipeline
from app.services.deepgram import DeepgramService

logger = logging.getLogger(__name__)


async def process_recording_blueprint_task(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process recording evaluation using Blueprint system
    
    Args:
        payload: {
            "recording_id": str,
            "blueprint_id": str (required)
        }
    """
    db = SessionLocal()
    recording = None
    evaluation = None
    try:
        recording_id = payload.get("recording_id")
        blueprint_id = payload.get("blueprint_id")
        if not blueprint_id:
            raise ValueError("blueprint_id is required for evaluation")
        
        logger.info(f"Processing recording {recording_id} with Blueprint system")
        
        # Get recording
        recording = db.query(Recording).filter(
            Recording.id == recording_id
        ).first()
        
        if not recording:
            logger.error(f"Recording {recording_id} not found")
            return {"status": "failed", "error": "Recording not found"}
        
        # Short-circuit if an evaluation already exists (idempotency)
        existing_eval = db.query(Evaluation).filter(
            Evaluation.recording_id == recording_id
        ).first()
        if existing_eval:
            if existing_eval.status in {EvaluationStatus.completed, EvaluationStatus.reviewed}:
                logger.info("Evaluation already completed/reviewed, returning existing result")
                return {
                    "status": existing_eval.status.value,
                    "evaluation_id": existing_eval.id,
                    "overall_score": existing_eval.overall_score,
                    "overall_passed": existing_eval.overall_passed,
                    "confidence_score": existing_eval.confidence_score,
                }
            if existing_eval.status == EvaluationStatus.pending:
                logger.warning("Evaluation already pending; not starting duplicate task")
                return {
                    "status": "pending",
                    "evaluation_id": existing_eval.id,
                    "error": "Evaluation already in progress"
                }

        if recording.status in {RecordingStatus.processing, RecordingStatus.queued}:
            logger.warning("Recording currently processing/queued; skipping duplicate evaluation task")
            return {"status": "failed", "error": f"Recording is currently {recording.status.value}"}

        blueprint = db.query(QABlueprint).filter(
            QABlueprint.id == blueprint_id
        ).first()
        
        if not blueprint or blueprint.status != BlueprintStatus.published:
            raise ValueError(f"Blueprint {blueprint_id} not found or not published")
        if blueprint.company_id != recording.company_id:
            raise ValueError("Blueprint does not belong to recording company")
        if not blueprint.compiled_flow_version_id:
            raise ValueError(f"Blueprint {blueprint_id} not compiled")

        # Mark evaluation intent up-front for observability/idempotency
        evaluation = db.query(Evaluation).filter(
            Evaluation.recording_id == recording_id
        ).first()
        if evaluation:
            evaluation.status = EvaluationStatus.pending
        else:
            evaluation = Evaluation(
                recording_id=recording_id,
                company_id=recording.company_id,
                overall_score=0,
                overall_passed=False,
                requires_human_review=False,
                status=EvaluationStatus.pending,
            )
            db.add(evaluation)

        # Persist linkage now so failures still reflect the chosen blueprint
        evaluation.blueprint_id = blueprint.id
        evaluation.compiled_flow_version_id = blueprint.compiled_flow_version_id
        evaluation.company_id = recording.company_id

        # Transition to processing only after validations
        recording.status = RecordingStatus.processing
        db.commit()
        
        # Check if transcript exists, if not, transcribe the audio
        transcript = db.query(Transcript).filter(
            Transcript.recording_id == recording_id
        ).first()
        
        if not transcript:
            logger.info(f"Transcript not found for recording {recording_id}, transcribing audio...")
            
            # Transcribe audio using Deepgram
            deepgram_service = DeepgramService()

            try:
                transcription_result = await deepgram_service.transcribe(recording.file_url)
                
                # Create Transcript record
                transcript = Transcript(
                    recording_id=recording_id,
                    transcript_text=transcription_result["transcript"],
                    diarized_segments=transcription_result["diarized_segments"],
                    transcription_confidence=transcription_result.get("confidence", 0.0),
                    sentiment_analysis=transcription_result.get("sentiment_analysis"),
                    deepgram_confidence=transcription_result.get("confidence")
                )
                db.add(transcript)
                db.commit()
                db.refresh(transcript)
                
                logger.info(f"Transcription completed for recording {recording_id}")
            except Exception as e:
                logger.error(f"Transcription failed for recording {recording_id}: {e}", exc_info=True)
                raise ValueError(f"Failed to transcribe audio: {str(e)}")
        
        # Run evaluation pipeline
        pipeline = EvaluationPipeline()
        evaluation_results = pipeline.evaluate_recording(
            recording_id=recording_id,
            compiled_flow_version_id=blueprint.compiled_flow_version_id,
            db=db,
            company_config={}
        )
        
        final_eval = evaluation_results["final_evaluation"]
        
        evaluation.recording_id = recording_id
        evaluation.company_id = recording.company_id
        evaluation.blueprint_id = blueprint_id
        evaluation.compiled_flow_version_id = blueprint.compiled_flow_version_id
        evaluation.overall_score = final_eval.get("overall_score", 0)
        evaluation.overall_passed = final_eval.get("overall_passed", False)
        evaluation.requires_human_review = final_eval.get("requires_human_review", False)
        evaluation.confidence_score = final_eval.get("confidence_score")
        evaluation.deterministic_results = evaluation_results["deterministic_results"]
        evaluation.llm_stage_evaluations = evaluation_results["llm_stage_evaluations"]
        evaluation.final_evaluation = final_eval
        evaluation.status = EvaluationStatus.completed
        
        recording.status = RecordingStatus.completed
        db.commit()
        
        logger.info(f"Recording {recording_id} evaluation completed")
        
        return {
            "status": "completed",
            "evaluation_id": evaluation.id,
            "overall_score": final_eval.get("overall_score"),
            "overall_passed": final_eval.get("overall_passed"),
            "confidence_score": final_eval.get("confidence_score"),
            "confidence_breakdown": final_eval.get("confidence_breakdown"),
            "explanation": final_eval.get("explanation"),
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Recording processing failed: {e}", exc_info=True)
        
        try:
            if recording is not None:
                recording.status = RecordingStatus.failed
                recording.error_message = str(e)
                db.commit()
        except Exception:
            db.rollback()

        try:
            if evaluation is not None:
                evaluation.status = EvaluationStatus.failed
                evaluation.final_evaluation = (evaluation.final_evaluation or {})
                evaluation.final_evaluation["error"] = str(e)
                db.commit()
        except Exception:
            db.rollback()
        
        return {
            "status": "failed",
            "error": str(e)
        }
    finally:
        db.close()

