"""
Sandbox Worker - Phase 9
Cloud Tasks handler for sandbox evaluations
"""

import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.sandbox import SandboxRun, SandboxResult, SandboxRunStatus
from app.models.qa_blueprint import QABlueprint

logger = logging.getLogger(__name__)


async def sandbox_evaluate_job_handler(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle sandbox evaluation job from Cloud Tasks
    
    Args:
        payload: {
            "sandbox_run_id": str,
            "blueprint_id": str,
            "recording_id": str (optional),
            "transcript": str (optional)
        }
    """
    logger.info(f"Sandbox job handler called with payload keys: {list(payload.keys())}")
    db = SessionLocal()
    sandbox_run = None
    sandbox_run_id = None
    try:
        sandbox_run_id = payload.get("sandbox_run_id")
        blueprint_id = payload.get("blueprint_id")
        
        logger.info(f"Processing sandbox run {sandbox_run_id} for blueprint {blueprint_id}")
        
        sandbox_run = db.query(SandboxRun).filter(
            SandboxRun.id == sandbox_run_id
        ).first()
        
        if not sandbox_run:
            logger.error(f"Sandbox run {sandbox_run_id} not found")
            return {"status": "failed", "error": "Sandbox run not found"}
        
        sandbox_run.status = SandboxRunStatus.running
        db.commit()
        db.refresh(sandbox_run)
        logger.info(f"Sandbox run {sandbox_run_id} status updated to running")
        
        try:
            # 1. Get transcript - create temporary Recording/Transcript if needed
            recording_id = payload.get("recording_id")
            transcript_text = payload.get("transcript")
            transcript_segments = []
            temp_recording_id = None
            
            if recording_id:
                # Get transcript from existing recording
                from app.models.transcript import Transcript
                from app.models.recording import Recording, RecordingStatus
                transcript = db.query(Transcript).filter(
                    Transcript.recording_id == recording_id
                ).first()
                
                if transcript:
                    transcript_text = transcript.transcript_text
                    transcript_segments = transcript.diarized_segments or []
            elif transcript_text:
                # Create temporary Recording and Transcript for sandbox
                from app.models.transcript import Transcript
                from app.models.recording import Recording, RecordingStatus
                import uuid
                
                # Parse transcript text into segments (basic parsing - split by lines)
                lines = transcript_text.strip().split('\n')
                segments = []
                for i, line in enumerate(lines):
                    if ':' in line:
                        parts = line.split(':', 1)
                        speaker = parts[0].strip().lower()
                        text = parts[1].strip()
                        # Normalize speaker names
                        if 'customer' in speaker or 'client' in speaker:
                            speaker_role = "customer"
                        else:
                            speaker_role = "agent"
                        
                        segments.append({
                            "speaker": speaker_role,
                            "text": text,
                            "start": float(i * 10),  # Approximate timestamps
                            "end": float((i + 1) * 10),
                            "confidence": 1.0
                        })
                    else:
                        # If no speaker label, assume agent
                        segments.append({
                            "speaker": "agent",
                            "text": line.strip(),
                            "start": float(i * 10),
                            "end": float((i + 1) * 10),
                            "confidence": 1.0
                        })
                
                if not segments:
                    # Fallback: single segment with all text
                    segments = [{
                        "speaker": "agent",
                        "text": transcript_text,
                        "start": 0.0,
                        "end": 10.0,
                        "confidence": 1.0
                    }]
                
                transcript_segments = segments
                
                # Create temporary Recording
                # Use sandbox_run_id directly (it's already a UUID, max 36 chars)
                # The "sandbox-" prefix would make it 44 chars, exceeding the 36 char limit
                temp_recording_id = str(sandbox_run_id)
                temp_recording = Recording(
                    id=temp_recording_id,
                    company_id=sandbox_run.company_id,
                    uploaded_by_user_id=sandbox_run.created_by,
                    file_name=f"sandbox-transcript-{sandbox_run_id}.txt",
                    file_url=f"sandbox://transcript-{sandbox_run_id}",
                    status=RecordingStatus.completed,
                    duration_seconds=int(len(segments) * 10)
                )
                db.add(temp_recording)
                
                # Create temporary Transcript
                temp_transcript = Transcript(
                    recording_id=temp_recording_id,
                    transcript_text=transcript_text,
                    diarized_segments=segments,
                    transcription_confidence=1.0
                )
                db.add(temp_transcript)
                db.commit()  # Commit to ensure Recording and Transcript are available
                
                recording_id = temp_recording_id
                logger.info(f"Created temporary Recording ({temp_recording_id}) and Transcript for sandbox run {sandbox_run_id}")
            
            if not transcript_segments:
                raise ValueError("No transcript available")
            
            # 2. Get blueprint and compiled version
            blueprint = db.query(QABlueprint).filter(
                QABlueprint.id == blueprint_id
            ).first()
            
            if not blueprint or not blueprint.compiled_flow_version_id:
                raise ValueError("Blueprint not found or not compiled")
            
            from app.models.compiled_artifacts import CompiledFlowVersion
            compiled_flow_version = db.query(CompiledFlowVersion).filter(
                CompiledFlowVersion.id == blueprint.compiled_flow_version_id
            ).first()
            
            if not compiled_flow_version:
                raise ValueError("Compiled flow version not found")
            
            # 3. Run evaluation pipeline
            # Note: LLM calls within the pipeline have timeouts (60s default)
            # If the pipeline hangs, it's likely due to an LLM call timeout which will be caught
            from app.services.evaluation_pipeline import EvaluationPipeline
            pipeline = EvaluationPipeline()
            
            logger.info(f"Starting evaluation pipeline for recording {recording_id}")
            evaluation_results = pipeline.evaluate_recording(
                recording_id=recording_id,
                compiled_flow_version_id=compiled_flow_version.id,
                db=db,
                company_config={}
            )
            logger.info(f"Evaluation pipeline completed successfully")
            
            # 4. Store results
            result = SandboxResult(
                sandbox_run_id=sandbox_run_id,
                transcript_snapshot={"segments_count": len(transcript_segments)},
                detection_output=evaluation_results["deterministic_results"],
                llm_stage_outputs=evaluation_results["llm_stage_evaluations"],
                final_evaluation=evaluation_results["final_evaluation"],
                cost_estimate={
                    "estimated_cost": 0.01,  # Placeholder
                    "tokens_used": 0  # Placeholder
                }
            )
            db.add(result)
            db.flush()
            
            sandbox_run.result_id = result.id
            sandbox_run.status = SandboxRunStatus.succeeded
            db.commit()
            
        except Exception as e:
            logger.error(f"Sandbox evaluation failed: {e}", exc_info=True)
            import traceback
            error_traceback = traceback.format_exc()
            logger.error(f"Full traceback: {error_traceback}")
            
            # Ensure status is updated even if there's an error
            try:
                db.refresh(sandbox_run)
                sandbox_run.status = SandboxRunStatus.failed
                
                # Store error in result
                try:
                    result = SandboxResult(
                        sandbox_run_id=sandbox_run_id,
                        logs={"error": str(e), "traceback": error_traceback},
                        final_evaluation={
                            "error": str(e),
                            "overall_score": 0,
                            "overall_passed": False
                        }
                    )
                    db.add(result)
                    db.flush()
                    sandbox_run.result_id = result.id
                except Exception as result_error:
                    logger.error(f"Failed to create error result: {result_error}", exc_info=True)
                
                db.commit()
                logger.info(f"Sandbox run {sandbox_run_id} status updated to failed")
            except Exception as commit_error:
                logger.error(f"Failed to update sandbox run status: {commit_error}", exc_info=True)
                db.rollback()
                # Try one more time with a fresh session
                try:
                    db.refresh(sandbox_run)
                    sandbox_run.status = SandboxRunStatus.failed
                    db.commit()
                except:
                    pass
            
            return {
                "status": "failed",
                "error": str(e)
            }
        
        logger.info(f"Sandbox run {sandbox_run_id} completed")
        
        return {
            "status": "succeeded",
            "sandbox_run_id": sandbox_run_id
        }
        
    except Exception as e:
        logger.error(f"Sandbox job failed with outer exception: {e}", exc_info=True)
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        try:
            db.rollback()
            if sandbox_run:
                db.refresh(sandbox_run)
                sandbox_run.status = SandboxRunStatus.failed
                db.commit()
                logger.info(f"Sandbox run {sandbox_run_id if sandbox_run else 'unknown'} status updated to failed in outer handler")
        except Exception as final_error:
            logger.error(f"Failed to update status in outer exception handler: {final_error}", exc_info=True)
        
        return {
            "status": "failed",
            "error": str(e)
        }
    finally:
        try:
            db.close()
        except:
            pass

