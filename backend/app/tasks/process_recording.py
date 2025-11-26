"""
Recording Processing Task
Uses the Blueprint evaluation pipeline for all recordings.
Legacy FlowVersion pipeline has been removed.
"""

import logging
from typing import Optional

from app.tasks.process_recording_blueprint import process_recording_blueprint_task

logger = logging.getLogger(__name__)


async def process_recording_task(recording_id: str, blueprint_id: Optional[str] = None):
    """
    Background task to process recording using the Blueprint pipeline.
    If blueprint_id is not provided, the latest published blueprint for the company will be used.
    """
    from app.database import SessionLocal
    from app.models.recording import Recording
    
    db = SessionLocal()
    try:
        recording = db.query(Recording).filter(Recording.id == recording_id).first()
        if recording and recording.file_url and recording.file_url.startswith("sandbox://"):
            logger.info(f"Skipping sandbox recording {recording_id} - processed via sandbox evaluation pipeline")
            return
    finally:
        db.close()
    
    logger.info(f"Processing recording {recording_id} with Blueprint pipeline")
    payload = {"recording_id": recording_id}
    if blueprint_id:
        payload["blueprint_id"] = blueprint_id
    await process_recording_blueprint_task(payload)
