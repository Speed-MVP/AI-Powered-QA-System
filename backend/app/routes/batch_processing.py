"""
Batch Processing API Routes
Phase 4: Scale & Optimization
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.services.batch_processing import BatchProcessingService
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/batch", tags=["batch-processing"])

# Global batch processing service instance
batch_service = BatchProcessingService()


@router.post("/start")
async def start_batch_processing():
    """Start the batch processing system."""
    try:
        result = await batch_service.start_batch_processing()
        return {"success": result["success"], "data": result}
    except Exception as e:
        logger.error(f"Error starting batch processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_batch_processing():
    """Stop the batch processing system."""
    try:
        result = await batch_service.stop_batch_processing()
        return {"success": result["success"], "data": result}
    except Exception as e:
        logger.error(f"Error stopping batch processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_batch_processing_status():
    """Get current batch processing status and statistics."""
    try:
        status = await batch_service.get_batch_processing_status()
        return {"success": True, "data": status}
    except Exception as e:
        logger.error(f"Error getting batch processing status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/queue/recordings")
async def queue_recordings_for_batch_processing(recording_ids: List[str]):
    """Queue specific recordings for batch processing."""
    try:
        result = await batch_service.queue_recordings_for_batch_processing(recording_ids)
        return {"success": result["success"], "data": result}
    except Exception as e:
        logger.error(f"Error queuing recordings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/queue/pending")
async def queue_pending_recordings(limit: int = 100):
    """Queue all pending recordings for batch processing."""
    try:
        result = await batch_service.queue_pending_recordings(limit=limit)
        return {"success": result["success"], "data": result}
    except Exception as e:
        logger.error(f"Error queuing pending recordings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process/high-priority")
async def process_high_priority_batch(recording_ids: List[str], priority: str = "high"):
    """Process a high-priority batch immediately."""
    try:
        result = await batch_service.process_high_priority_batch(recording_ids, priority)
        return {"success": result["success"], "data": result}
    except Exception as e:
        logger.error(f"Error processing high-priority batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))











