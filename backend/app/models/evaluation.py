from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey, Text, Float, JSON, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import enum
import uuid


class EvaluationStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    reviewed = "reviewed"


class Evaluation(Base):
    __tablename__ = "evaluations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recording_id = Column(String(36), ForeignKey("recordings.id"), nullable=False, unique=True, index=True)
    policy_template_id = Column(String(36), ForeignKey("policy_templates.id"), nullable=False)
    evaluated_by_user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    overall_score = Column(Integer, nullable=False)
    resolution_detected = Column(Boolean, nullable=False)
    resolution_confidence = Column(Float, nullable=False)
    confidence_score = Column(Float, nullable=True)  # Phase 1: Overall AI confidence for human fallback routing
    requires_human_review = Column(Boolean, default=False)  # Phase 1: Flag for human review routing
    customer_tone = Column(JSONB, nullable=True)  # Stores customer emotion/tone analysis
    llm_analysis = Column(JSONB, nullable=False)
    status = Column(Enum(EvaluationStatus), default=EvaluationStatus.pending)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    recording = relationship("Recording", back_populates="evaluation")
    policy_template = relationship("PolicyTemplate", back_populates="evaluations")
    evaluated_by_user = relationship("User", back_populates="evaluations")
    category_scores = relationship("CategoryScore", back_populates="evaluation", cascade="all, delete-orphan")
    policy_violations = relationship("PolicyViolation", back_populates="evaluation", cascade="all, delete-orphan")
    human_review = relationship("HumanReview", uselist=False, back_populates="evaluation", cascade="all, delete-orphan")  # Phase 3
    versions = relationship("EvaluationVersion", back_populates="evaluation", cascade="all, delete-orphan", order_by="EvaluationVersion.version_number")  # Phase 4

