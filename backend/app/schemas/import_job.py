from datetime import datetime
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class ImportJobResponse(BaseModel):
    id: str
    company_id: str
    status: str
    file_name: Optional[str] = None
    rows_total: Optional[int] = None
    rows_processed: Optional[int] = None
    rows_failed: Optional[int] = None
    validation_errors: Optional[List[Dict[str, Any]]] = Field(default=None)
    created_by: str
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
