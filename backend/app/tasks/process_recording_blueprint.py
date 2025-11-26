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
            "blueprint_id": str (optional, will use active published blueprint)
        }
    """
    db = SessionLocal()
    try:
        recording_id = payload.get("recording_id")
        blueprint_id = payload.get("blueprint_id")
        
        logger.info(f"Processing recording {recording_id} with Blueprint system")
        
        # Get recording
        recording = db.query(Recording).filter(
            Recording.id == recording_id
        ).first()
        
        if not recording:
            logger.error(f"Recording {recording_id} not found")
            return {"status": "failed", "error": "Recording not found"}
        
        recording.status = RecordingStatus.processing
        db.commit()
        
        # Get active blueprint
        if not blueprint_id:
            # Find active published blueprint for company
            blueprint = db.query(QABlueprint).filter(
                QABlueprint.company_id == recording.company_id,
                QABlueprint.status == BlueprintStatus.published
            ).order_by(QABlueprint.updated_at.desc()).first()
            
            if not blueprint:
                raise ValueError("No published blueprint found for company")
            
            blueprint_id = blueprint.id
        
        blueprint = db.query(QABlueprint).filter(
            QABlueprint.id == blueprint_id
        ).first()
        
        if not blueprint or blueprint.status != BlueprintStatus.published:
            raise ValueError(f"Blueprint {blueprint_id} not found or not published")
        
        if not blueprint.compiled_flow_version_id:
            raise ValueError(f"Blueprint {blueprint_id} not compiled")
        
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
        
        # Create or update evaluation
        evaluation = db.query(Evaluation).filter(
            Evaluation.recording_id == recording_id
        ).first()
        
        final_eval = evaluation_results["final_evaluation"]
        
        if not evaluation:
            evaluation = Evaluation(
                recording_id=recording_id,
                company_id=recording.company_id,
                blueprint_id=blueprint_id,
                compiled_flow_version_id=blueprint.compiled_flow_version_id,
                overall_score=final_eval.get("overall_score", 0),
                overall_passed=final_eval.get("overall_passed", False),
                requires_human_review=final_eval.get("requires_human_review", False),
                confidence_score=final_eval.get("confidence_score"),
                deterministic_results=evaluation_results["deterministic_results"],
                llm_stage_evaluations=evaluation_results["llm_stage_evaluations"],
                final_evaluation=final_eval,
                status=EvaluationStatus.completed
            )
            db.add(evaluation)
        else:
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
            "status": "succeeded",
            "evaluation_id": evaluation.id,
            "overall_score": final_eval.get("overall_score"),
            "overall_passed": final_eval.get("overall_passed")
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Recording processing failed: {e}", exc_info=True)
        
        if recording:
            recording.status = RecordingStatus.failed
            recording.error_message = str(e)
            db.commit()
        
        return {
            "status": "failed",
            "error": str(e)
        }
    finally:
        db.close()

