"""
Evaluation Model - Phase 9
New evaluation schema for Blueprint-based evaluations
"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Float, Boolean, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import uuid
import enum


class EvaluationStatus(str, enum.Enum):
    """Evaluation status"""
    pending = "pending"
    completed = "completed"
    reviewed = "reviewed"
    failed = "failed"


class Evaluation(Base):
    """Evaluation record for Blueprint-based evaluations"""
    __tablename__ = "evaluations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recording_id = Column(String(36), ForeignKey("recordings.id"), nullable=False, unique=True, index=True)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False, index=True)
    blueprint_id = Column(String(36), ForeignKey("qa_blueprints.id"), nullable=True, index=True)
    blueprint_version_id = Column(String(36), ForeignKey("qa_blueprint_versions.id"), nullable=True)
    compiled_flow_version_id = Column(String(36), ForeignKey("compiled_flow_versions.id"), nullable=True, index=True)
    
    # Scores
    overall_score = Column(Integer, nullable=False)
    overall_passed = Column(Boolean, nullable=False, default=False)
    requires_human_review = Column(Boolean, nullable=False, default=False)
    confidence_score = Column(Float, nullable=True)
    
    # Evaluation results (JSONB)
    deterministic_results = Column(JSONB, nullable=True)  # Detection engine output
    llm_stage_evaluations = Column(JSONB, nullable=True)  # Per-stage LLM evaluations
    final_evaluation = Column(JSONB, nullable=True)  # Final scoring snapshot
    
    # Metadata
    status = Column(SQLEnum(EvaluationStatus), nullable=False, default=EvaluationStatus.pending, index=True)
    evaluated_by_user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    agent_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    team_id = Column(String(36), ForeignKey("teams.id"), nullable=True)
    
    # Reproducibility
    prompt_version = Column(String(20), nullable=True)
    model_version = Column(String(50), nullable=True)
    model_temperature = Column(Float, default=0.0)
    evaluation_seed = Column(String(50), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    recording = relationship("Recording", back_populates="evaluation")
    company = relationship("Company")
    blueprint = relationship("QABlueprint")
    agent = relationship("User", foreign_keys=[agent_id])
    evaluated_by_user = relationship("User", foreign_keys=[evaluated_by_user_id], back_populates="evaluations")
    team = relationship("Team", back_populates="evaluations")
    human_review = relationship("HumanReview", back_populates="evaluation", uselist=False)
