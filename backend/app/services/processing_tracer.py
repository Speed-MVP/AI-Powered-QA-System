from typing import Any, Optional
from app.models.recording_processing_event import RecordingProcessingEvent
import logging

logger = logging.getLogger(__name__)


class ProcessingTracer:
    """Persists fine-grained processing events for a recording."""

    def __init__(self, db_session):
        self.db = db_session

    def log(
        self,
        recording_id: str,
        stage: str,
        status: str,
        message: Optional[str] = None,
        event_metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        try:
            event = RecordingProcessingEvent(
                recording_id=recording_id,
                stage=stage,
                status=status,
                message=message,
                event_metadata=event_metadata,
            )
            self.db.add(event)
            self.db.commit()
        except Exception as exc:
            logger.warning(
                "Failed to persist processing event for recording %s stage %s: %s",
                recording_id,
                stage,
                exc,
                exc_info=True,
            )
            self.db.rollback()

