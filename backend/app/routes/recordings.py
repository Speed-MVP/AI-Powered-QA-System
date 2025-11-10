from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.recording import Recording, RecordingStatus
from app.middleware.auth import get_current_user
from app.services.storage import StorageService
from app.tasks.process_recording import process_recording_task
from app.schemas.recording import RecordingCreate, RecordingResponse, RecordingListResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/signed-url")
async def get_signed_url(
    file_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get signed URL for direct upload to GCP Storage"""
    storage = StorageService()
    signed_url = storage.get_signed_upload_url(
        file_name=file_name,
        company_id=current_user.company_id
    )
    
    # Generate file URL for storage
    file_url = storage.get_public_url(f"{current_user.company_id}/{file_name}")
    
    return {
        "signed_url": signed_url,
        "file_url": file_url,
        "file_name": file_name
    }


@router.post("/upload-direct", response_model=RecordingResponse)
async def upload_file_direct(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload file directly through backend (avoids CORS issues)"""
    try:
        storage_service = StorageService()
        
        # Upload file to GCP Storage
        blob_name = f"{current_user.company_id}/{file.filename}"
        blob = storage_service.bucket.blob(blob_name)
        
        # Read file content
        content = await file.read()
        
        logger.info(f"Uploading file '{file.filename}' to bucket '{storage_service.bucket.name}' as '{blob_name}'")
        logger.info(f"File size: {len(content)} bytes, Content-Type: {file.content_type or 'audio/mpeg'}")
        
        # Upload file to GCP Storage
        try:
            blob.upload_from_string(content, content_type=file.content_type or "audio/mpeg")
            logger.info(f"Successfully uploaded file to GCP Storage: {blob_name}")
        except Exception as upload_error:
            error_msg = str(upload_error)
            logger.error(f"GCP Storage upload error: {error_msg}")
            if "403" in error_msg or "Permission" in error_msg or "permission" in error_msg:
                from app.config import settings
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission denied. Service account '{settings.gcp_client_email}' needs 'Storage Object Admin' role on bucket '{settings.gcp_bucket_name}'. Please check IAM permissions in GCP Console."
                )
            raise
        
        # Generate file URL
        file_url = storage_service.get_public_url(blob_name)
        
        # Create recording in DB
        recording = Recording(
            company_id=current_user.company_id,
            uploaded_by_user_id=current_user.id,
            file_name=file.filename,
            file_url=file_url,
            status=RecordingStatus.queued
        )
        db.add(recording)
        db.commit()
        db.refresh(recording)
        
        # Trigger background processing
        background_tasks.add_task(process_recording_task, recording.id)
        
        logger.info(f"Recording {recording.id} uploaded and queued for processing")
        
        return recording
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error uploading file: {error_msg}", exc_info=True)
        db.rollback()
        
        # Provide more helpful error message for bucket not found
        if "does not exist" in error_msg or "404" in error_msg:
            from app.config import settings
            raise HTTPException(
                status_code=404,
                detail=f"Bucket '{settings.gcp_bucket_name}' not found. Please check your GCP_BUCKET_NAME in .env file matches the actual bucket name in GCP Console."
            )
        
        raise HTTPException(status_code=500, detail=f"Upload failed: {error_msg}")


@router.post("/upload", response_model=RecordingResponse)
async def upload_recording(
    recording_data: RecordingCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create recording entry and trigger processing"""
    # Create recording in DB
    recording = Recording(
        company_id=current_user.company_id,
        uploaded_by_user_id=current_user.id,
        file_name=recording_data.file_name,
        file_url=recording_data.file_url,
        status=RecordingStatus.queued
    )
    db.add(recording)
    db.commit()
    db.refresh(recording)
    
    # Trigger background processing
    background_tasks.add_task(process_recording_task, recording.id)
    
    logger.info(f"Recording {recording.id} queued for processing")
    
    return recording


@router.get("/list", response_model=list[RecordingListResponse])
async def list_recordings(
    skip: int = 0,
    limit: int = 50,
    status: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List recordings for company"""
    query = db.query(Recording).filter(Recording.company_id == current_user.company_id)
    
    if status:
        try:
            status_enum = RecordingStatus(status)
            query = query.filter(Recording.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    recordings = query.order_by(Recording.uploaded_at.desc()).offset(skip).limit(limit).all()
    
    return recordings


@router.get("/{recording_id}", response_model=RecordingResponse)
async def get_recording(
    recording_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific recording"""
    recording = db.query(Recording).filter(
        Recording.id == recording_id,
        Recording.company_id == current_user.company_id
    ).first()
    
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    return recording


@router.delete("/{recording_id}")
async def delete_recording(
    recording_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete recording and its file from GCP bucket"""
    recording = db.query(Recording).filter(
        Recording.id == recording_id,
        Recording.company_id == current_user.company_id
    ).first()
    
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    try:
        # Delete file from GCP Storage
        storage_service = StorageService()
        # Extract blob name from file_url or construct it
        blob_name = f"{current_user.company_id}/{recording.file_name}"
        
        try:
            storage_service.delete_file(blob_name)
            logger.info(f"Deleted file from GCP Storage: {blob_name}")
        except Exception as storage_error:
            # Log error but continue with database deletion
            logger.warning(f"Failed to delete file from GCP Storage: {storage_error}")
        
        # Delete related evaluations, transcripts, etc. (cascade should handle this)
        # But we'll delete explicitly to be sure
        from app.models.evaluation import Evaluation
        from app.models.transcript import Transcript
        
        db.query(Evaluation).filter(Evaluation.recording_id == recording_id).delete()
        db.query(Transcript).filter(Transcript.recording_id == recording_id).delete()
        
        # Delete recording
        db.delete(recording)
        db.commit()
        
        logger.info(f"Deleted recording {recording_id} and related data")
        
        return {"message": "Recording deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting recording: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete recording: {str(e)}")


@router.post("/{recording_id}/reevaluate")
async def reevaluate_recording(
    recording_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Re-evaluate a recording"""
    recording = db.query(Recording).filter(
        Recording.id == recording_id,
        Recording.company_id == current_user.company_id
    ).first()
    
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    # Delete existing evaluation and transcript to start fresh
    from app.models.evaluation import Evaluation
    from app.models.transcript import Transcript
    
    db.query(Evaluation).filter(Evaluation.recording_id == recording_id).delete()
    db.query(Transcript).filter(Transcript.recording_id == recording_id).delete()
    
    # Reset recording status
    recording.status = RecordingStatus.queued
    recording.processed_at = None
    db.commit()
    
    # Trigger background processing
    background_tasks.add_task(process_recording_task, recording.id)
    
    logger.info(f"Re-evaluation triggered for recording {recording_id}")
    
    return {"message": "Re-evaluation started", "recording_id": recording_id}


@router.get("/{recording_id}/download-url")
async def get_download_url(
    recording_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get signed download URL for audio file"""
    recording = db.query(Recording).filter(
        Recording.id == recording_id,
        Recording.company_id == current_user.company_id
    ).first()
    
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    try:
        storage_service = StorageService()
        # Extract blob name from file_url or construct it
        blob_name = f"{current_user.company_id}/{recording.file_name}"
        
        logger.info(f"Generating download URL for recording {recording_id}: blob_name={blob_name}")
        
        # Check if blob exists
        blob = storage_service.bucket.blob(blob_name)
        if not blob.exists():
            logger.error(f"Blob not found: {blob_name}")
            raise HTTPException(status_code=404, detail=f"Audio file not found in storage: {recording.file_name}")
        
        # Generate signed URL for download (valid for 1 hour)
        signed_url = storage_service.get_signed_download_url(blob_name, expiration_minutes=60)
        
        logger.info(f"Successfully generated download URL for recording {recording_id}")
        
        return {
            "download_url": signed_url,
            "file_name": recording.file_name,
            "expires_in_minutes": 60
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating download URL for recording {recording_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate download URL: {str(e)}")

