"""
Tasks Router - Phase 4
Handles Cloud Tasks webhook endpoints for background jobs
"""

from fastapi import APIRouter, Request, HTTPException, Header
from typing import Dict, Any
import logging
import json

from app.tasks.compile_blueprint_job import compile_blueprint_job_handler
from app.tasks.sandbox_worker import sandbox_evaluate_job_handler
from app.tasks.process_recording_blueprint import process_recording_blueprint_task

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.post("/compile-blueprint")
async def handle_compile_blueprint_task(request: Request):
    """Handle compile blueprint Cloud Task"""
    try:
        payload = await request.json()
        result = await compile_blueprint_job_handler(payload)
        
        if result.get("status") == "failed":
            return {"status": "error", "result": result}, 500
        
        return {"status": "ok", "result": result}
        
    except Exception as e:
        logger.error(f"Task handler error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sandbox-evaluate")
async def handle_sandbox_evaluate_task(request: Request):
    """Handle sandbox evaluate Cloud Task"""
    try:
        payload = await request.json()
        result = await sandbox_evaluate_job_handler(payload)
        
        if result.get("status") == "failed":
            return {"status": "error", "result": result}, 500
        
        return {"status": "ok", "result": result}
        
    except Exception as e:
        logger.error(f"Task handler error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process-recording")
async def handle_process_recording_task(request: Request):
    """Handle process recording Cloud Task"""
    try:
        payload = await request.json()
        result = await process_recording_blueprint_task(payload)
        
        if result.get("status") == "failed":
            return {"status": "error", "result": result}, 500
        
        return {"status": "ok", "result": result}
        
    except Exception as e:
        logger.error(f"Task handler error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

