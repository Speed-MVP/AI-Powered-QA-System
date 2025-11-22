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

    # MVP Evaluation Improvements: Reproducibility metadata
    prompt_id = Column(String(100), nullable=True)
    prompt_version = Column(String(20), nullable=True)
    model_version = Column(String(50), nullable=True)
    model_temperature = Column(Float, default=0.0)
    model_top_p = Column(Float, default=1.0)
    llm_raw = Column(JSONB, nullable=True)  # Store full LLM response payload
    rubric_version = Column(String(20), nullable=True)
    evaluation_seed = Column(String(50), nullable=True)  # Optional trace id
    
    # Phase 1: Agent/Team associations
    agent_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    team_id = Column(String(36), ForeignKey("teams.id"), nullable=True)
    
    # Phase 3-7: Standardized Phases - Store evaluation results
    deterministic_results = Column(JSONB, nullable=True)  # Phase 3: DeterministicRuleEngine output
    llm_stage_evaluations = Column(JSONB, nullable=True)  # Phase 4: LLM stage evaluations
    final_evaluation = Column(JSONB, nullable=True)  # Phase 6: FinalEvaluation from RubricScorer
    flow_version_id = Column(String(36), ForeignKey("flow_versions.id"), nullable=True)  # Link to FlowVersion used
    rubric_template_id = Column(String(36), ForeignKey("rubric_templates.id"), nullable=True)  # Link to RubricTemplate used
    
    # Relationships
    recording = relationship("Recording", back_populates="evaluation")
    evaluated_by_user = relationship("User", back_populates="evaluations", foreign_keys=[evaluated_by_user_id])
    agent = relationship("User", foreign_keys=[agent_id])
    team = relationship("Team", back_populates="evaluations")
    category_scores = relationship("CategoryScore", back_populates="evaluation", cascade="all, delete-orphan")
    human_review = relationship("HumanReview", uselist=False, back_populates="evaluation", cascade="all, delete-orphan")  # Phase 3
    rule_engine_results = relationship("RuleEngineResults", back_populates="evaluation", cascade="all, delete-orphan")  # MVP Evaluation Improvements
    versions = relationship("EvaluationVersion", back_populates="evaluation", cascade="all, delete-orphan", order_by="EvaluationVersion.version_number")  # Phase 4

