"""
Cloud Tasks Service - Phase 2
Wrapper for GCP Cloud Tasks to enqueue background jobs
"""

import json
import logging
import time
from typing import Optional, Dict, Any

from google.cloud import tasks_v2
from google.oauth2 import service_account
from google.protobuf import timestamp_pb2

from app.config import settings

logger = logging.getLogger(__name__)


class CloudTasksService:
    """Service for enqueueing Cloud Tasks"""
    
    def __init__(self):
        self.client = None
        self.project_id = settings.gcp_project_id
        self.location = settings.gcp_cloud_tasks_location or "us-central1"
        self.queue_name = settings.gcp_cloud_tasks_queue_name or "default"
        self.service_url = settings.gcp_cloud_run_service_url
        self.service_account_email = settings.gcp_client_email

        credentials = None
        if settings.gcp_client_email and settings.gcp_private_key:
            private_key = settings.gcp_private_key.replace("\\n", "\n")
            credentials_info = {
                "type": "service_account",
                "project_id": settings.gcp_project_id,
                "private_key_id": "",
                "private_key": private_key,
                "client_email": settings.gcp_client_email,
                "client_id": "",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{settings.gcp_client_email.replace('@', '%40')}",
                "universe_domain": "googleapis.com",
            }
            credentials = service_account.Credentials.from_service_account_info(
                credentials_info,
                scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )
            logger.info(
                "Initialized Cloud Tasks client using service account from environment variables"
            )
        elif settings.gcp_credentials_path:
            credentials = service_account.Credentials.from_service_account_file(
                settings.gcp_credentials_path,
                scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )
            logger.info("Initialized Cloud Tasks client using credentials file")
        else:
            logger.info("Initialized Cloud Tasks client using default credentials")
        
        if self.project_id and self.location and self.queue_name and self.service_url:
            try:
                if credentials:
                    self.client = tasks_v2.CloudTasksClient(credentials=credentials)
                else:
                    self.client = tasks_v2.CloudTasksClient()
            except Exception:
                # If it fails, BackgroundTasks fallback will be used
                self.client = None
    
    def _get_queue_path(self) -> Optional[str]:
        """Get the full queue path"""
        if not self.client:
            return None
        return self.client.queue_path(self.project_id, self.location, self.queue_name)
    
    def enqueue_task(
        self,
        task_handler: str,
        payload: Dict[str, Any],
        delay_seconds: int = 0,
        task_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Enqueue a Cloud Task
        
        Args:
            task_handler: The endpoint path that will handle this task (e.g., "/api/tasks/compile-blueprint")
            payload: The task payload (will be JSON serialized)
            delay_seconds: Delay before task execution
            task_id: Optional unique task ID (for idempotency)
        
        Returns:
            Task name if successful, None otherwise
        """
        if not self.client or not self.service_url:
            # Return None silently - fallback will be used
            return None
        
        try:
            queue_path = self._get_queue_path()
            if not queue_path:
                return None
            
            # Create task
            task = {
                "http_request": {
                    "http_method": tasks_v2.HttpMethod.POST,
                    "url": f"{self.service_url}{task_handler}",
                    "headers": {
                        "Content-Type": "application/json",
                    },
                    "body": json.dumps(payload).encode(),
                }
            }

            if self.service_account_email:
                task["http_request"]["oidc_token"] = {
                    "service_account_email": self.service_account_email,
                    "audience": self.service_url,
                }
            
            # Set delay if specified
            if delay_seconds > 0:
                timestamp = timestamp_pb2.Timestamp()
                timestamp.FromSeconds(int(time.time()) + delay_seconds)
                task["schedule_time"] = timestamp
            
            # Set task ID for idempotency
            if task_id:
                task["name"] = f"{queue_path}/tasks/{task_id}"
            
            # Create the task
            response = self.client.create_task(
                request={"parent": queue_path, "task": task}
            )
            
            logger.info(f"Enqueued Cloud Task: {response.name}")
            return response.name
            
        except Exception as e:
            logger.error(f"Failed to enqueue Cloud Task: {e}", exc_info=True)
            return None
    
    def enqueue_compile_job(
        self,
        blueprint_id: str,
        blueprint_version_id: str,
        compile_options: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Enqueue a blueprint compile job
        
        Args:
            blueprint_id: The blueprint ID to compile
            blueprint_version_id: The blueprint version ID
            compile_options: Compiler options
            user_id: User who triggered the compile
        
        Returns:
            Task name if successful, None otherwise
        """
        payload = {
            "blueprint_id": blueprint_id,
            "blueprint_version_id": blueprint_version_id,
            "compile_options": compile_options or {},
            "user_id": user_id,
        }
        
        # Use blueprint_version_id as task_id for idempotency
        task_id = f"compile-{blueprint_version_id}"
        
        return self.enqueue_task(
            task_handler="/api/tasks/compile-blueprint",
            payload=payload,
            task_id=task_id
        )
    
    def enqueue_sandbox_job(
        self,
        sandbox_run_id: str,
        blueprint_id: str,
        recording_id: Optional[str] = None,
        transcript: Optional[str] = None
    ) -> Optional[str]:
        """
        Enqueue a sandbox evaluation job
        
        Args:
            sandbox_run_id: The sandbox run ID
            blueprint_id: The blueprint ID
            recording_id: Optional recording ID (for audio)
            transcript: Optional transcript text (for sync runs)
        
        Returns:
            Task name if successful, None otherwise
        """
        payload = {
            "sandbox_run_id": sandbox_run_id,
            "blueprint_id": blueprint_id,
            "recording_id": recording_id,
            "transcript": transcript,
        }
        
        task_id = f"sandbox-{sandbox_run_id}"
        
        return self.enqueue_task(
            task_handler="/api/tasks/sandbox-evaluate",
            payload=payload,
            task_id=task_id
        )


# Singleton instance
cloud_tasks_service = CloudTasksService()

