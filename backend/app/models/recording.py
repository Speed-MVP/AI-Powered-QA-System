from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import enum
import uuid


class RecordingStatus(str, enum.Enum):
    queued = "queued"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class Recording(Base):
    __tablename__ = "recordings"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False, index=True)
    uploaded_by_user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_url = Column(Text, nullable=False)
    duration_seconds = Column(Integer, nullable=True)
    status = Column(Enum(RecordingStatus), default=RecordingStatus.queued, index=True)
    error_message = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow, index=True)
    processed_at = Column(DateTime, nullable=True)
    
    # Phase 1: Agent/Team associations
    agent_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    team_id = Column(String(36), ForeignKey("teams.id"), nullable=True)
    
    # Relationships
    company = relationship("Company", back_populates="recordings")
    uploaded_by_user = relationship("User", back_populates="recordings", foreign_keys=[uploaded_by_user_id])
    agent = relationship("User", foreign_keys=[agent_id])
    team = relationship("Team", back_populates="recordings")
    transcript = relationship("Transcript", uselist=False, back_populates="recording")
    evaluation = relationship("Evaluation", uselist=False, back_populates="recording")

