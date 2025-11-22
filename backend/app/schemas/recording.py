from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.recording import RecordingStatus


class RecordingCreate(BaseModel):
    file_name: str
    file_url: str
    # Phase 7: No longer using policy_template_id - evaluations use FlowVersion + RubricTemplate


class RecordingResponse(BaseModel):
    id: str
    file_name: str
    file_url: str
    status: str
    duration_seconds: Optional[int] = None
    error_message: Optional[str] = None
    uploaded_at: datetime
    processed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class RecordingListResponse(BaseModel):
    id: str
    file_name: str
    status: str
    duration_seconds: Optional[int] = None
    uploaded_at: datetime
    processed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

