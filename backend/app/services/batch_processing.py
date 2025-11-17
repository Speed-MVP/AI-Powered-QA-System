"""
Batch Processing Service for Asynchronous Call Evaluation
Phase 4: Scale & Optimization
"""

from app.database import SessionLocal
from app.models.recording import Recording, RecordingStatus
from app.tasks.process_recording import process_recording_task
from typing import List, Dict, Any, Optional
import asyncio
import logging
from datetime import datetime, timedelta
import concurrent.futures
import threading
import time

logger = logging.getLogger(__name__)


class BatchProcessingService:
    """
    Phase 4: Batch inference system for processing hundreds of calls asynchronously.
    Queue + worker system with confidence-based routing.
    """

    def __init__(self, max_workers: int = 4, batch_size: int = 10):
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self.processing_queue = asyncio.Queue()
        self.is_running = False
        self.stats = {
            "processed": 0,
            "failed": 0,
            "queued": 0,
            "avg_processing_time": 0.0
        }

    async def start_batch_processing(self) -> Dict[str, Any]:
        """Start the batch processing system."""
        if self.is_running:
            return {"success": False, "error": "Batch processing already running"}

        self.is_running = True
        logger.info(f"Starting batch processing with {self.max_workers} workers")

        # Start worker tasks
        workers = []
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._batch_worker(f"worker-{i+1}"))
            workers.append(worker)

        # Start queue monitor
        monitor = asyncio.create_task(self._queue_monitor())

        return {
            "success": True,
            "workers": self.max_workers,
            "batch_size": self.batch_size,
            "status": "running"
        }

    async def stop_batch_processing(self) -> Dict[str, Any]:
        """Stop the batch processing system."""
        self.is_running = False
        await self.processing_queue.put(None)  # Signal workers to stop

        logger.info("Stopping batch processing system")
        return {"success": True, "status": "stopped"}

    async def queue_recordings_for_batch_processing(self, recording_ids: List[str]) -> Dict[str, Any]:
        """Queue multiple recordings for batch processing."""
        queued_count = 0

        for recording_id in recording_ids:
            # Validate recording exists and is in correct state
            db = SessionLocal()
            try:
                recording = db.query(Recording).filter(Recording.id == recording_id).first()
                if recording and recording.status == RecordingStatus.queued:
                    await self.processing_queue.put(recording_id)
                    queued_count += 1
                    self.stats["queued"] += 1
                else:
                    logger.warning(f"Recording {recording_id} not eligible for batch processing")
            finally:
                db.close()

        logger.info(f"Queued {queued_count} recordings for batch processing")
        return {
            "success": True,
            "queued": queued_count,
            "total_queued": self.stats["queued"]
        }

    async def queue_pending_recordings(self, limit: int = 100) -> Dict[str, Any]:
        """Queue all pending recordings for batch processing."""
        db = SessionLocal()
        try:
            pending_recordings = db.query(Recording).filter(
                Recording.status == RecordingStatus.queued
            ).limit(limit).all()

            recording_ids = [r.id for r in pending_recordings]
            return await self.queue_recordings_for_batch_processing(recording_ids)
        finally:
            db.close()

    async def get_batch_processing_status(self) -> Dict[str, Any]:
        """Get current batch processing status and statistics."""
        db = SessionLocal()
        try:
            # Get queue statistics
            queued_count = db.query(Recording).filter(
                Recording.status == RecordingStatus.queued
            ).count()

            processing_count = db.query(Recording).filter(
                Recording.status == RecordingStatus.processing
            ).count()

            completed_today = db.query(Recording).filter(
                Recording.status == RecordingStatus.completed,
                Recording.processed_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            ).count()

            failed_today = db.query(Recording).filter(
                Recording.status == RecordingStatus.failed,
                Recording.uploaded_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            ).count()

            return {
                "is_running": self.is_running,
                "workers": self.max_workers,
                "batch_size": self.batch_size,
                "queue_size": self.processing_queue.qsize(),
                "pending_recordings": queued_count,
                "processing_recordings": processing_count,
                "completed_today": completed_today,
                "failed_today": failed_today,
                "stats": self.stats,
                "throughput_estimate": self._estimate_throughput()
            }
        finally:
            db.close()

    async def _batch_worker(self, worker_id: str):
        """Individual batch worker that processes recordings."""
        logger.info(f"Batch worker {worker_id} started")

        while self.is_running:
            try:
                # Get next recording from queue
                recording_id = await asyncio.wait_for(
                    self.processing_queue.get(),
                    timeout=5.0
                )

                if recording_id is None:  # Shutdown signal
                    break

                # Process the recording
                start_time = time.time()
                await self._process_single_recording(recording_id)
                processing_time = time.time() - start_time

                # Update stats
                self.stats["processed"] += 1
                self.stats["avg_processing_time"] = (
                    (self.stats["avg_processing_time"] * (self.stats["processed"] - 1)) +
                    processing_time
                ) / self.stats["processed"]

                self.processing_queue.task_done()

                logger.info(f"Batch worker {worker_id} processed recording {recording_id}")
            except asyncio.TimeoutError:
                # No work available, continue loop
                continue
            except Exception as e:
                logger.error(f"Batch worker {worker_id} error: {e}")
                self.stats["failed"] += 1
                continue

        logger.info(f"Batch worker {worker_id} stopped")

    async def _process_single_recording(self, recording_id: str):
        """Process a single recording using the existing pipeline."""
        try:
            await process_recording_task(recording_id)
        except Exception as e:
            logger.error(f"Failed to process recording {recording_id}: {e}")
            # Update recording status to failed
            db = SessionLocal()
            try:
                recording = db.query(Recording).filter(Recording.id == recording_id).first()
                if recording:
                    recording.status = RecordingStatus.failed
                    recording.error_message = str(e)[:500]
                    db.commit()
            finally:
                db.close()

    async def _queue_monitor(self):
        """Monitor queue health and performance."""
        while self.is_running:
            try:
                await asyncio.sleep(60)  # Check every minute

                status = await self.get_batch_processing_status()
                queue_size = status["queue_size"]

                # Auto-scale queue if needed (in production, could add more workers)
                if queue_size > 50 and self.max_workers < 8:
                    logger.warning(f"Large queue backlog ({queue_size} items). Consider scaling workers.")
                elif queue_size == 0:
                    logger.info("Queue empty - no pending work")

            except Exception as e:
                logger.error(f"Queue monitor error: {e}")

    def _estimate_throughput(self) -> Dict[str, Any]:
        """Estimate current processing throughput."""
        if self.stats["processed"] == 0:
            return {"calls_per_hour": 0, "avg_time_seconds": 0}

        avg_time = self.stats["avg_processing_time"]
        calls_per_hour = 3600 / avg_time if avg_time > 0 else 0

        return {
            "calls_per_hour": round(calls_per_hour, 1),
            "avg_time_seconds": round(avg_time, 1),
            "estimated_daily_capacity": round(calls_per_hour * 24)
        }

    async def process_high_priority_batch(self, recording_ids: List[str], priority: str = "high") -> Dict[str, Any]:
        """
        Process a high-priority batch immediately (bypasses normal queue).
        Useful for urgent evaluations or VIP customers.
        """
        logger.info(f"Processing high-priority batch of {len(recording_ids)} recordings")

        # Create tasks for parallel processing
        tasks = []
        for recording_id in recording_ids:
            task = asyncio.create_task(self._process_single_recording(recording_id))
            tasks.append(task)

        # Wait for all to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        successful = sum(1 for r in results if not isinstance(r, Exception))
        failed = len(results) - successful

        logger.info(f"High-priority batch completed: {successful} successful, {failed} failed")

        return {
            "success": True,
            "total": len(recording_ids),
            "successful": successful,
            "failed": failed,
            "priority": priority
        }
