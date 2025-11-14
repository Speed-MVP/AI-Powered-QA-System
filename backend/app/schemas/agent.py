from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional


class AgentBase(BaseModel):
    email: EmailStr
    full_name: str
    team_id: Optional[str] = None


class AgentCreate(AgentBase):
    pass


class AgentUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    team_id: Optional[str] = None


class AgentTeamMembershipResponse(BaseModel):
    membership_id: str
    team_id: str
    team_name: Optional[str] = None
    role: Optional[str] = None


class AgentResponse(BaseModel):
    id: str
    company_id: str
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    team_memberships: List[AgentTeamMembershipResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True
