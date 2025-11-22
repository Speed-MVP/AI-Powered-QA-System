"""
Phase 3: Rule Engine V2 - Results Model
Stores deterministic rule evaluation results from Rule Engine V2.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import uuid


class RuleEngineResultsV2(Base):
    __tablename__ = "rule_engine_results_v2"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    evaluation_id = Column(String(36), ForeignKey("evaluations.id"), nullable=False, unique=True)
    policy_rules_version = Column(Integer, nullable=True)  # Version of policy_rules used for evaluation

    # Core results
    rule_results = Column(JSONB, nullable=False)  # Structured rule evaluation results

    # Performance metrics
    execution_time_ms = Column(Integer, nullable=True)      # How long evaluation took
    transcript_segments_count = Column(Integer, nullable=True)  # Number of segments processed
    rules_evaluated_count = Column(Integer, nullable=True)  # Number of rules evaluated

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    evaluation = relationship("Evaluation", back_populates="rule_engine_results_v2")

    def __repr__(self):
        return f"<RuleEngineResultsV2(id='{self.id}', evaluation_id='{self.evaluation_id}', rules_evaluated={self.rules_evaluated_count})>"







