"""
Recording Processing Task
Always uses Phase 7 pipeline (FlowVersion + RubricTemplate + ComplianceRule).
Legacy PolicyTemplate system has been removed.
"""

from app.tasks.process_recording_phase7 import process_recording_phase7
import logging

logger = logging.getLogger(__name__)


async def process_recording_task(recording_id: str):
    """
    Background task to process recording.
    Always uses Phase 7 pipeline (FlowVersion + RubricTemplate + ComplianceRule).
    Legacy PolicyTemplate system has been removed.
    """
    logger.info(f"Processing recording {recording_id} with Phase 7 pipeline")
    await process_recording_phase7(recording_id)
