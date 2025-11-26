"""
Sandbox API Routes - Phase 9
Endpoints for sandbox test evaluations
"""

from fastapi import APIRouter, Depends, HTTPException, Header, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import logging
import uuid

from app.database import get_db
from app.models.user import User
from app.models.qa_blueprint import QABlueprint
from app.models.sandbox import SandboxRun, SandboxResult, SandboxRunStatus, SandboxInputType
from app.middleware.auth import get_current_user
from app.middleware.permissions import require_company_access
from app.services.cloud_tasks import cloud_tasks_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/blueprints", tags=["sandbox"])


@router.post("/{blueprint_id}/sandbox-evaluate")
async def sandbox_evaluate(
    blueprint_id: str,
    request_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    """Run sandbox evaluation (sync for transcript, async for audio)"""
    blueprint = db.query(QABlueprint).filter(
        QABlueprint.id == blueprint_id
    ).first()
    
    if not blueprint:
        raise HTTPException(status_code=404, detail="Blueprint not found")
    
    require_company_access(blueprint.company_id, current_user)
    
    mode = request_data.get("mode", "sync")
    input_data = request_data.get("input", {})
    transcript = input_data.get("transcript")
    recording_id = input_data.get("recording_id")
    
    # Check if blueprint is compiled
    if not blueprint.compiled_flow_version_id:
        # Check if blueprint has been published (has versions)
        from app.models.qa_blueprint_version import QABlueprintVersion
        from app.models.qa_blueprint_compiler_map import QABlueprintCompilerMap
        
        latest_version = db.query(QABlueprintVersion).filter(
            QABlueprintVersion.blueprint_id == blueprint_id
        ).order_by(QABlueprintVersion.version_number.desc()).first()
        
        logger.info(f"Checking compilation status for blueprint {blueprint_id}. Latest version: {latest_version.id if latest_version else None}")
        
        if latest_version:
            # Check both blueprint_version.compiled_flow_version_id and compiler_map
            compiled_flow_version_id = None
            
            # First, check if blueprint_version has compiled_flow_version_id set
            if latest_version.compiled_flow_version_id:
                compiled_flow_version_id = latest_version.compiled_flow_version_id
                logger.info(f"Found compiled_flow_version_id in blueprint_version: {compiled_flow_version_id}")
            else:
                # Check compiler_map
                compiler_map = db.query(QABlueprintCompilerMap).filter(
                    QABlueprintCompilerMap.blueprint_version_id == latest_version.id
                ).first()
                
                logger.info(f"Compiler map found: {compiler_map is not None}. flow_version_id: {compiler_map.flow_version_id if compiler_map else None}")
                
                if compiler_map and compiler_map.flow_version_id:
                    compiled_flow_version_id = compiler_map.flow_version_id
                    logger.info(f"Found compiled_flow_version_id in compiler_map: {compiled_flow_version_id}")
            
            if compiled_flow_version_id:
                # Compilation completed but blueprint.compiled_flow_version_id wasn't updated
                # Update both blueprint and blueprint_version
                logger.info(f"Blueprint {blueprint_id} has compiled version {compiled_flow_version_id} but blueprint.compiled_flow_version_id is not set. Updating...")
                blueprint.compiled_flow_version_id = compiled_flow_version_id
                if not latest_version.compiled_flow_version_id:
                    latest_version.compiled_flow_version_id = compiled_flow_version_id
                db.commit()
                db.refresh(blueprint)
                logger.info(f"Successfully updated blueprint {blueprint_id}.compiled_flow_version_id to {compiled_flow_version_id}")
            else:
                # No compilation found - trigger it now synchronously
                logger.info(f"Blueprint {blueprint_id} version {latest_version.id} is not compiled. Triggering compilation synchronously...")
                from app.tasks.compile_blueprint_job import compile_blueprint_job_handler
                
                try:
                    payload = {
                        "blueprint_id": blueprint_id,
                        "blueprint_version_id": latest_version.id,
                        "compile_options": {},
                        "user_id": current_user.id
                    }
                    # Run compilation synchronously (since sandbox needs it immediately)
                    result = await compile_blueprint_job_handler(payload)
                    
                    if result.get("status") == "succeeded":
                        compiled_flow_version_id = result.get("compiled_flow_version_id")
                        if compiled_flow_version_id:
                            # Refresh blueprint from DB to get updated state
                            db.refresh(blueprint)
                            blueprint.compiled_flow_version_id = compiled_flow_version_id
                            if not latest_version.compiled_flow_version_id:
                                latest_version.compiled_flow_version_id = compiled_flow_version_id
                            db.commit()
                            db.refresh(blueprint)
                            logger.info(f"Successfully compiled and updated blueprint {blueprint_id}.compiled_flow_version_id = {compiled_flow_version_id}")
                        else:
                            raise HTTPException(
                                status_code=500,
                                detail="Compilation completed but no compiled_flow_version_id was returned"
                            )
                    else:
                        errors = result.get("errors", [])
                        error_msg = f"Compilation failed: {errors[0].get('message', 'Unknown error')}" if errors else "Compilation failed"
                        logger.error(f"Blueprint compilation failed: {error_msg}")
                        raise HTTPException(
                            status_code=500,
                            detail=error_msg
                        )
                except HTTPException:
                    raise
                except Exception as e:
                    logger.error(f"Failed to compile blueprint: {e}", exc_info=True)
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to compile blueprint: {str(e)}"
                    )
        else:
            logger.warning(f"Blueprint {blueprint_id} has not been published yet (no versions found)")
            raise HTTPException(
                status_code=400,
                detail="Blueprint must be published before running sandbox evaluation. Please publish the blueprint first."
            )
    
    # Create sandbox run
    sandbox_run = SandboxRun(
        company_id=current_user.company_id,
        created_by=current_user.id,
        blueprint_id=blueprint_id,
        input_type=SandboxInputType.transcript if transcript else SandboxInputType.audio,
        input_location=recording_id or f"transcript-{uuid.uuid4()}",
        status=SandboxRunStatus.queued,
        idempotency_key=idempotency_key
    )
    db.add(sandbox_run)
    db.commit()
    db.refresh(sandbox_run)
    
    if mode == "sync" and transcript:
        # For sync mode, run evaluation immediately in background
        # Import here to avoid circular imports
        from app.tasks.sandbox_worker import sandbox_evaluate_job_handler
        import asyncio
        import threading
        
        logger.info(f"SYNC MODE: Preparing to run sandbox evaluation for run {sandbox_run.id}")
        logger.info(f"Transcript length: {len(transcript) if transcript else 0}")
        
        # Create a wrapper function that can be called in a thread
        def run_sandbox_evaluation():
            """Run sandbox evaluation in background thread"""
            try:
                logger.info(f"[THREAD] Starting sandbox evaluation for run {sandbox_run.id}")
                payload = {
                    "sandbox_run_id": str(sandbox_run.id),
                    "blueprint_id": blueprint_id,
                    "recording_id": None,
                    "transcript": transcript
                }
                logger.info(f"[THREAD] Payload prepared: {list(payload.keys())}")
                
                # Create new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    logger.info(f"[THREAD] Event loop created, calling sandbox_evaluate_job_handler...")
                    result = loop.run_until_complete(sandbox_evaluate_job_handler(payload))
                    logger.info(f"[THREAD] Sandbox evaluation completed: {result.get('status', 'unknown')}")
                except Exception as async_error:
                    logger.error(f"[THREAD] Async error in sandbox evaluation: {async_error}", exc_info=True)
                    import traceback
                    logger.error(f"[THREAD] Traceback: {traceback.format_exc()}")
                finally:
                    loop.close()
                    logger.info(f"[THREAD] Event loop closed")
            except Exception as e:
                logger.error(f"[THREAD] Sandbox evaluation thread failed: {e}", exc_info=True)
                import traceback
                logger.error(f"[THREAD] Full traceback: {traceback.format_exc()}")
        
        # Run in a background thread to ensure it executes
        logger.info(f"[MAIN] Starting background thread for sandbox run {sandbox_run.id}")
        thread = threading.Thread(target=run_sandbox_evaluation, daemon=False, name=f"SandboxEval-{sandbox_run.id}")
        thread.start()
        logger.info(f"[MAIN] Background thread started. Thread is_alive: {thread.is_alive()}")
        
        return {
            "run_id": sandbox_run.id,
            "status": "queued",
            "message": "Evaluation running in background"
        }
    else:
        # Enqueue async job (Cloud Tasks or background fallback)
        job_id = None
        try:
            job_id = cloud_tasks_service.enqueue_sandbox_job(
                sandbox_run_id=sandbox_run.id,
                blueprint_id=blueprint_id,
                recording_id=recording_id,
                transcript=transcript
            )
        except Exception as e:
            logger.warning(f"Failed to enqueue sandbox job (Cloud Tasks may not be configured): {e}")
            job_id = None
        
        # If Cloud Tasks is not available, run in background
        if not job_id:
            logger.warning("Cloud Tasks not available. Running sandbox evaluation in background...")
            from app.tasks.sandbox_worker import sandbox_evaluate_job_handler
            
            async def run_async_evaluation():
                """Run sandbox evaluation asynchronously"""
                try:
                    payload = {
                        "sandbox_run_id": sandbox_run.id,
                        "blueprint_id": blueprint_id,
                        "recording_id": recording_id,
                        "transcript": transcript
                    }
                    result = await sandbox_evaluate_job_handler(payload)
                    logger.info(f"Background sandbox evaluation completed: {result.get('status', 'unknown')}")
                except Exception as e:
                    logger.error(f"Background sandbox evaluation failed: {e}", exc_info=True)
            
            # Run in background
            background_tasks.add_task(run_async_evaluation)
            job_id = f"local-{sandbox_run.id}"
        
        return {
            "run_id": sandbox_run.id,
            "status": "queued",
            "job_id": job_id
        }


@router.get("/{blueprint_id}/sandbox-runs/{run_id}")
async def get_sandbox_run(
    blueprint_id: str,
    run_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get sandbox run result"""
    sandbox_run = db.query(SandboxRun).filter(
        SandboxRun.id == run_id,
        SandboxRun.blueprint_id == blueprint_id
    ).first()
    
    if not sandbox_run:
        raise HTTPException(status_code=404, detail="Sandbox run not found")
    
    require_company_access(sandbox_run.company_id, current_user)
    
    result_data = None
    if sandbox_run.result:
        result_data = {
            "final_evaluation": sandbox_run.result.final_evaluation,
            "detection_output": sandbox_run.result.detection_output,
            "cost_estimate": sandbox_run.result.cost_estimate
        }
    
    return {
        "run_id": sandbox_run.id,
        "status": sandbox_run.status.value,
        "created_at": sandbox_run.created_at.isoformat(),
        "result": result_data
    }

