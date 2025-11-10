from sqlalchemy import Column, String, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import uuid
import enum


class TeamRole(str, enum.Enum):
    agent = "agent"
    team_lead = "team_lead"
    supervisor = "supervisor"


class AgentTeamMembership(Base):
    __tablename__ = "agent_team_memberships"
    __table_args__ = (
        UniqueConstraint('agent_id', 'team_id', name='uq_agent_team_memberships_agent_id_team_id'),
    )
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    team_id = Column(String(36), ForeignKey("teams.id"), nullable=False, index=True)
    role = Column(String(50), default="agent", nullable=False)  # Fixed: NOT NULL to match database
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    agent = relationship("User", foreign_keys=[agent_id])
    team = relationship("Team", back_populates="memberships")
    created_by_user = relationship("User", foreign_keys=[created_by])


class AgentTeamChange(Base):
    __tablename__ = "agent_team_changes"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_type = Column(String(50), nullable=False)  # 'agent', 'team', 'membership'
    entity_id = Column(String(36), nullable=False)
    change_type = Column(String(50), nullable=False)  # 'created', 'updated', 'deleted'
    field_name = Column(String(255), nullable=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    changed_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    changed_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False, index=True)
    
    # Relationships
    changed_by_user = relationship("User", foreign_keys=[changed_by])
    company = relationship("Company")

