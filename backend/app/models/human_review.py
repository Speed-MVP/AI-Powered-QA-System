"""
Human Review Model
Human Review is for score overrides, audit, and compliance only.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Numeric, Integer, Boolean, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import enum
import uuid


class ReviewStatus(str, enum.Enum):
    pending = "pending"
    in_review = "in_review"
    completed = "completed"
    disputed = "disputed"


class HumanReview(Base):
    """
    Human-reviewed evaluations for score overrides, audit, and compliance.
    
    Purpose:
    - Score override: Reviewer can modify stage and final scores
    - Audit trail: Track why scores were changed
    - Compliance: Enterprise requirement for human override capabilities
    - Dispute resolution: Agents can dispute, supervisors can override
    
    """
    __tablename__ = "human_reviews"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recording_id = Column(String(36), ForeignKey("recordings.id"), nullable=False)
    evaluation_id = Column(String(36), ForeignKey("evaluations.id"), nullable=False, unique=True)
    reviewer_user_id = Column(String(36), ForeignKey("users.id"), nullable=True)  # Nullable for anonymous reviews
    review_status = Column(Enum(ReviewStatus), nullable=True, default=ReviewStatus.pending)

    # Human evaluation data
    human_stage_scores = Column(JSONB, nullable=True)  # List of stage scores: [{"stage_id": "...", "score": 80}, ...]
    human_violations = Column(JSONB, nullable=True)  # list of violations with evidence
    ai_scores = Column(JSONB, nullable=True)  # snapshot of AI scores for comparison
    delta = Column(JSONB, nullable=True)  # computed ai->human differences
    reviewer_notes = Column(Text, nullable=True)
    
    # Additional fields used by the code
    ai_score_accuracy = Column(Numeric(3, 1), nullable=True)
    human_overall_score = Column(Integer, nullable=True)
    ai_recommendation = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)

    # Relationships
    evaluation = relationship("Evaluation", back_populates="human_review")
    reviewer = relationship("User", back_populates="human_reviews", foreign_keys=[reviewer_user_id])


