from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import uuid


class Team(Base):
    __tablename__ = "teams"
    __table_args__ = (
        UniqueConstraint('company_id', 'name', name='uq_teams_company_id_name'),
    )
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    updated_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    company = relationship("Company", back_populates="teams")
    created_by_user = relationship("User", foreign_keys=[created_by])
    updated_by_user = relationship("User", foreign_keys=[updated_by])
    memberships = relationship("AgentTeamMembership", back_populates="team", cascade="all, delete-orphan")
    recordings = relationship("Recording", back_populates="team")
    evaluations = relationship("Evaluation", back_populates="team")


