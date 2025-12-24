"""
Sandbox Worker - Phase 9
Cloud Tasks handler for sandbox evaluations
"""

import logging
import re
from typing import Dict, Any, List, Tuple, Optional
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.sandbox import SandboxRun, SandboxResult, SandboxRunStatus
from app.models.qa_blueprint import QABlueprint

logger = logging.getLogger(__name__)


# Patterns for detecting speaker roles
CUSTOMER_PATTERNS = [
    'customer', 'client', 'caller', 'user', 'member', 'patient', 
    'guest', 'visitor', 'buyer', 'consumer', 'subscriber'
]
AGENT_PATTERNS = [
    'agent', 'rep', 'representative', 'support', 'advisor', 'specialist',
    'associate', 'operator', 'staff', 'employee', 'csr', 'service'
]


def detect_speaker_role(speaker_label: str) -> str:
    """
    Detect if a speaker label refers to an agent or customer.
    
    Args:
        speaker_label: The raw speaker label from the transcript
        
    Returns:
        Either "agent" or "customer"
    """
    label_lower = speaker_label.lower().strip()
    
    # Check for customer patterns first (more specific)
    for pattern in CUSTOMER_PATTERNS:
        if pattern in label_lower:
            return "customer"
    
    # Check for agent patterns
    for pattern in AGENT_PATTERNS:
        if pattern in label_lower:
            return "agent"
    
    # Default to agent if unsure
    return "agent"


def parse_transcript_line(line: str) -> Optional[Tuple[str, str]]:
    """
    Parse a transcript line to extract speaker and text.
    
    Handles formats like:
    - "Agent: Hello, how can I help?"
    - "Customer (John): I have a question"
    - "Rep: What seems to be the issue?"
    
    Args:
        line: A single line of transcript text
        
    Returns:
        Tuple of (speaker_role, text) or None if line is empty/unparseable
    """
    if not line or not line.strip():
        return None
    
    line = line.strip()
    
    # Try to split by colon
    if ':' in line:
        # Find the first colon that's likely a speaker separator
        # (not part of a time like "10:30" or URL)
        colon_match = re.match(r'^([^:]{1,50}):\s*(.+)$', line)
        if colon_match:
            speaker_raw = colon_match.group(1).strip()
            text = colon_match.group(2).strip()
            
            # Check if this looks like a valid speaker label
            # (not a time stamp, not too long, contains letters)
            if (len(speaker_raw) <= 50 and 
                re.search(r'[a-zA-Z]', speaker_raw) and
                not re.match(r'^\d{1,2}:\d{2}', speaker_raw)):
                
                speaker_role = detect_speaker_role(speaker_raw)
                return (speaker_role, text)
    
    # No valid speaker found - return line as text with default speaker
    return ("agent", line)


def parse_transcript_text(transcript_text: str) -> List[Dict[str, Any]]:
    """
    Parse raw transcript text into segments.
    
    Args:
        transcript_text: Raw transcript text with speaker labels
        
    Returns:
        List of segment dictionaries with speaker, text, and timestamps
    """
    segments = []
    lines = transcript_text.strip().split('\n')
    
    line_number = 0
    for line in lines:
        parsed = parse_transcript_line(line)
        if parsed is None:
            continue
        
        speaker_role, text = parsed
        
        # Skip empty text
        if not text:
            continue
        
        # Calculate approximate timestamps (10 seconds per segment)
        start_time = float(line_number * 10)
        end_time = float((line_number + 1) * 10)
        
        segment = {
            "speaker": speaker_role,
            "text": text,
            # Include both timestamp field naming conventions for compatibility
            "start": start_time,
            "end": end_time,
            "start_time": start_time,
            "end_time": end_time,
            "confidence": 1.0
        }
        segments.append(segment)
        line_number += 1
    
    return segments


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
                
                # Parse transcript text into segments using improved parser
                segments = parse_transcript_text(transcript_text)
                
                # Log parsing results for debugging
                agent_count = sum(1 for s in segments if s.get("speaker") == "agent")
                customer_count = sum(1 for s in segments if s.get("speaker") == "customer")
                logger.info(f"Parsed transcript: {len(segments)} segments ({agent_count} agent, {customer_count} customer)")
                
                if segments:
                    # Log first few segments for debugging
                    for i, seg in enumerate(segments[:3]):
                        logger.debug(f"  Segment {i}: speaker={seg.get('speaker')}, text='{seg.get('text', '')[:50]}...'")
                
                if not segments:
                    # Fallback: single segment with all text
                    logger.warning("No segments parsed from transcript, using fallback single-segment approach")
                    segments = [{
                        "speaker": "agent",
                        "text": transcript_text,
                        "start": 0.0,
                        "end": 10.0,
                        "start_time": 0.0,
                        "end_time": 10.0,
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

