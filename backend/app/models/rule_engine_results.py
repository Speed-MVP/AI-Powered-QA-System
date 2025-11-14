"""
Rule Engine Results Model
MVP Evaluation Improvements
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import uuid


class RuleEngineResults(Base):
    """
    Stores deterministic rule engine results for each recording/evaluation.
    MVP Evaluation Improvements: Rule engine expansion and return format.
    """
    __tablename__ = "rule_engine_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recording_id = Column(String(36), ForeignKey("recordings.id"), nullable=False)
    evaluation_id = Column(String(36), ForeignKey("evaluations.id"), nullable=True)
    rules = Column(JSONB, nullable=False)  # map(rule_name -> {hit: bool, evidence: [...], severity: int})
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    recording = relationship("Recording", back_populates="rule_engine_results")
    evaluation = relationship("Evaluation", back_populates="rule_engine_results")
