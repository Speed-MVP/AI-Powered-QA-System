from google.cloud import storage
from google.oauth2 import service_account
from app.config import settings
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class StorageService:
    def __init__(self):
        # Create credentials from environment variables if provided
        credentials = None
        if settings.gcp_client_email and settings.gcp_private_key:
            # Replace escaped newlines with actual newlines
            private_key = settings.gcp_private_key.replace('\\n', '\n')
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
                "universe_domain": "googleapis.com"
            }
            credentials = service_account.Credentials.from_service_account_info(
                credentials_info,
                scopes=['https://www.googleapis.com/auth/cloud-platform']
            )
            logger.info(f"Using GCP credentials from environment variables (Service Account: {settings.gcp_client_email})")
        elif settings.gcp_credentials_path:
            # Fallback to JSON file if provided
            credentials = service_account.Credentials.from_service_account_file(settings.gcp_credentials_path)
            logger.info(f"Using GCP credentials from file: {settings.gcp_credentials_path}")
        else:
            # Use default credentials (Application Default Credentials)
            logger.info("Using default GCP credentials (Application Default Credentials)")
        
        if credentials:
            self.client = storage.Client(credentials=credentials, project=settings.gcp_project_id)
        else:
            self.client = storage.Client(project=settings.gcp_project_id)
        
        # Log bucket name for debugging
        logger.info(f"Initializing StorageService with bucket: {settings.gcp_bucket_name}")
        
        try:
            self.bucket = self.client.bucket(settings.gcp_bucket_name)
            # Try to verify bucket exists, but don't fail if we don't have bucket.get permission
            # We'll fail on actual operations if permissions are insufficient
            try:
                self.bucket.reload()
                logger.info(f"Successfully connected to bucket: {settings.gcp_bucket_name}")
            except Exception as reload_error:
                error_msg = str(reload_error)
                if "403" in error_msg or "Permission" in error_msg or "permission" in error_msg:
                    logger.warning(f"Could not verify bucket permissions (this is okay if service account has object-level permissions): {error_msg}")
                    logger.warning(f"Bucket '{settings.gcp_bucket_name}' will be used, but ensure service account has 'Storage Object Admin' or 'Storage Admin' role")
                else:
                    logger.error(f"Failed to connect to bucket '{settings.gcp_bucket_name}': {error_msg}")
                    raise
        except Exception as e:
            error_msg = str(e)
            if "does not exist" in error_msg or "404" in error_msg:
                logger.error(f"Bucket '{settings.gcp_bucket_name}' not found. Please check your GCP_BUCKET_NAME in .env file")
            elif "403" in error_msg or "Permission" in error_msg or "permission" in error_msg:
                logger.error(f"Permission denied for bucket '{settings.gcp_bucket_name}'")
                logger.error(f"Service account '{settings.gcp_client_email}' needs Storage permissions")
                logger.error(f"Grant 'Storage Object Admin' or 'Storage Admin' role to the service account in GCP Console")
            else:
                logger.error(f"Failed to initialize bucket '{settings.gcp_bucket_name}': {error_msg}")
            raise
    
    def get_signed_upload_url(self, file_name: str, company_id: str, expiration_minutes: int = 15):
        """Generate signed URL for direct browser upload"""
        blob_name = f"{company_id}/{file_name}"
        blob = self.bucket.blob(blob_name)
        
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=expiration_minutes),
            method="PUT"
        )
        
        return signed_url
    
    def get_signed_download_url(self, file_path: str, expiration_minutes: int = 60):
        """Generate signed URL for file download"""
        blob = self.bucket.blob(file_path)
        
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=expiration_minutes),
            method="GET"
        )
        
        return signed_url
    
    def get_public_url(self, file_path: str):
        """Get public URL for file"""
        return f"https://storage.googleapis.com/{self.bucket.name}/{file_path}"
    
    def delete_file(self, file_path: str):
        """Delete file from storage"""
        blob = self.bucket.blob(file_path)
        blob.delete()
        logger.info(f"Deleted file: {file_path}")

