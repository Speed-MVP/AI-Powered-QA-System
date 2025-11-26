"""
Sandbox Models - Phase 9
Models for sandbox test evaluations
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import uuid
import enum


class SandboxRunStatus(str, enum.Enum):
    """Sandbox run status"""
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    canceled = "canceled"


class SandboxInputType(str, enum.Enum):
    """Sandbox input type"""
    transcript = "transcript"
    audio = "audio"


class SandboxRun(Base):
    """Sandbox run record"""
    __tablename__ = "sandbox_runs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False, index=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    blueprint_id = Column(String(36), ForeignKey("qa_blueprints.id"), nullable=True, index=True)
    blueprint_version_id = Column(String(36), ForeignKey("qa_blueprint_versions.id"), nullable=True)
    input_type = Column(SQLEnum(SandboxInputType), nullable=False)
    input_location = Column(String(500), nullable=True)  # S3/GCS path or hash
    status = Column(SQLEnum(SandboxRunStatus), nullable=False, default=SandboxRunStatus.queued, index=True)
    result_id = Column(String(36), ForeignKey("sandbox_results.id"), nullable=True)
    idempotency_key = Column(String(255), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    company = relationship("Company")
    blueprint = relationship("QABlueprint")
    result = relationship("SandboxResult", uselist=False, foreign_keys=[result_id])


class SandboxResult(Base):
    """Sandbox evaluation result"""
    __tablename__ = "sandbox_results"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sandbox_run_id = Column(String(36), ForeignKey("sandbox_runs.id"), nullable=False, unique=True, index=True)
    transcript_snapshot = Column(JSONB, nullable=True)  # Redacted transcript or hash
    detection_output = Column(JSONB, nullable=True)
    llm_stage_outputs = Column(JSONB, nullable=True)  # Optionally redacted
    final_evaluation = Column(JSONB, nullable=True)
    logs = Column(JSONB, nullable=True)  # Compile/eval logs, errors
    cost_estimate = Column(JSONB, nullable=True)  # llm_tokens, transcription_seconds, estimated_cost
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    sandbox_run = relationship("SandboxRun", foreign_keys=[sandbox_run_id])


class SandboxQuota(Base):
    """Sandbox quota per company"""
    __tablename__ = "sandbox_quota"
    
    company_id = Column(String(36), ForeignKey("companies.id"), primary_key=True)
    monthly_allowed_runs = Column(Integer, nullable=False, default=100)
    monthly_used_runs = Column(Integer, nullable=False, default=0)
    last_reset = Column(DateTime, nullable=False, default=datetime.utcnow)

