"""
QA Blueprint Behavior Model - Phase 2
Atomic behaviors inside stages
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Numeric, Integer, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import uuid
import enum


class BehaviorType(str, enum.Enum):
    """Behavior type"""
    required = "required"
    optional = "optional"
    forbidden = "forbidden"
    critical = "critical"


class DetectionMode(str, enum.Enum):
    """Detection mode"""
    semantic = "semantic"
    exact_phrase = "exact_phrase"
    hybrid = "hybrid"


class CriticalAction(str, enum.Enum):
    """Critical action when behavior is violated"""
    fail_stage = "fail_stage"
    fail_overall = "fail_overall"
    flag_only = "flag_only"


class QABlueprintBehavior(Base):
    __tablename__ = "qa_blueprint_behaviors"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    stage_id = Column(String(36), ForeignKey("qa_blueprint_stages.id", ondelete="CASCADE"), nullable=False, index=True)
    behavior_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)  # guidance for reviewers / examples
    behavior_type = Column(SQLEnum(BehaviorType), nullable=False, default=BehaviorType.required)
    detection_mode = Column(SQLEnum(DetectionMode), nullable=False, default=DetectionMode.semantic)
    phrases = Column(JSONB, nullable=True)  # array of strings or array of objects {text, match_type}; only used if detection_mode != semantic
    weight = Column(Numeric(5, 2), nullable=False, default=0)  # weight contribution within stage (0-100)
    critical_action = Column(SQLEnum(CriticalAction), nullable=True)  # only relevant if behavior_type='critical'
    ui_order = Column(Integer, nullable=False, default=0)  # UI ordering within a stage
    extra_metadata = Column(JSONB, nullable=True, name="metadata")  # e.g., suggested synonyms, sample utterances, language hints, tone constraints
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    stage = relationship("QABlueprintStage", back_populates="behaviors")
    
    def __repr__(self):
        return f"<QABlueprintBehavior(id='{self.id}', behavior_name='{self.behavior_name}', type={self.behavior_type.value}, weight={self.weight})>"

