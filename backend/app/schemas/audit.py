from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class AgentAuditLogResponse(BaseModel):
    id: str
    company_id: str
    entity_type: str
    entity_id: str
    change_type: str
    field_name: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    changed_by: str
    changed_at: datetime

    class Config:
        from_attributes = True
