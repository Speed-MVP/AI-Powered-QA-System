"""
Human Review and Fine-Tuning Dataset Models
Phase 3: Fine-Tuning & Self-Learning
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
    Human-reviewed evaluations for dataset capture and comparison.
    MVP Evaluation Improvements: Human-review dataset capture and storage schema.
    """
    __tablename__ = "human_reviews"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recording_id = Column(String(36), ForeignKey("recordings.id"), nullable=False)
    evaluation_id = Column(String(36), ForeignKey("evaluations.id"), nullable=False, unique=True)
    reviewer_user_id = Column(String(36), ForeignKey("users.id"), nullable=True)  # Nullable for anonymous reviews
    review_status = Column(Enum(ReviewStatus), nullable=True, default=ReviewStatus.pending)

    # Human evaluation data
    human_scores = Column(JSONB, nullable=True)  # category -> score (e.g., {"greeting": 80, "empathy": 60})
    human_violations = Column(JSONB, nullable=True)  # list of violations with evidence
    ai_scores = Column(JSONB, nullable=True)  # snapshot of AI scores for comparison
    delta = Column(JSONB, nullable=True)  # computed ai->human differences
    reviewer_notes = Column(Text, nullable=True)
    
    # Additional fields used by the code
    ai_score_accuracy = Column(Numeric(3, 1), nullable=True)
    human_overall_score = Column(Integer, nullable=True)
    human_category_scores = Column(JSONB, nullable=True)
    ai_recommendation = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)

    # Relationships
    evaluation = relationship("Evaluation", back_populates="human_review")
    reviewer = relationship("User", back_populates="human_reviews", foreign_keys=[reviewer_user_id])


class FineTuningDataset(Base):
    """
    Curated datasets for Gemini fine-tuning.
    Phase 3: Use labeled data to fine-tune Gemini on QA rubrics.
    """
    __tablename__ = "fine_tuning_datasets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Dataset composition
    total_samples = Column(Integer, default=0)
    training_samples = Column(Integer, default=0)
    validation_samples = Column(Integer, default=0)
    test_samples = Column(Integer, default=0)

    # Fine-tuning configuration
    model_version = Column(String(50), nullable=False)  # e.g., "gemini-1.5-pro"
    fine_tuning_job_id = Column(String(255), nullable=True)  # Vertex AI job ID
    fine_tuning_status = Column(String(50), nullable=True)  # "pending", "running", "completed", "failed"

    # Performance metrics
    baseline_accuracy = Column(Numeric(5, 2), nullable=True)  # Before fine-tuning
    fine_tuned_accuracy = Column(Numeric(5, 2), nullable=True)  # After fine-tuning
    human_agreement_score = Column(Numeric(5, 2), nullable=True)  # Agreement with human reviewers

    # Version control
    version = Column(String(20), nullable=False, default="1.0.0")
    is_active = Column(Boolean, default=False)  # Only one active dataset at a time

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    samples = relationship("FineTuningSample", back_populates="dataset", cascade="all, delete-orphan")


class FineTuningSample(Base):
    """
    Individual training samples for fine-tuning.
    Input: transcripts + structured features
    Output: category scores + violations
    """
    __tablename__ = "fine_tuning_samples"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(String(36), ForeignKey("fine_tuning_datasets.id"), nullable=False)

    # Input data
    transcript_text = Column(Text, nullable=False)
    diarized_segments = Column(JSONB, nullable=True)
    sentiment_analysis = Column(JSONB, nullable=True)
    voice_baselines = Column(JSONB, nullable=True)

    # Additional features for fine-tuning
    call_metadata = Column(JSONB, nullable=True)  # duration, topic, company, etc.
    policy_template_id = Column(String(36), nullable=True)

    # Ground truth labels
    expected_category_scores = Column(JSONB, nullable=False)  # Human-reviewed scores
    expected_violations = Column(JSONB, nullable=True)  # Expected violations
    expected_overall_score = Column(Integer, nullable=False)

    # Sample metadata
    source_evaluation_id = Column(String(36), nullable=True)  # Original evaluation
    quality_score = Column(Numeric(3, 1), nullable=True)  # 1.0-5.0 quality rating
    difficulty_level = Column(String(20), nullable=True)  # "easy", "medium", "hard"

    # Fine-tuning usage
    split = Column(String(20), nullable=False)  # "train", "validation", "test"
    used_in_training = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    dataset = relationship("FineTuningDataset", back_populates="samples")


class ModelPerformance(Base):
    """
    Track model performance over time for continuous learning.
    Phase 3: Continuous learning loop with weekly retraining.
    """
    __tablename__ = "model_performance"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Model version
    model_version = Column(String(50), nullable=False)
    fine_tuning_dataset_id = Column(String(36), ForeignKey("fine_tuning_datasets.id"), nullable=True)

    # Performance metrics
    accuracy_score = Column(Numeric(5, 2), nullable=True)  # Overall accuracy
    precision_score = Column(Numeric(5, 2), nullable=True)  # Precision
    recall_score = Column(Numeric(5, 2), nullable=True)  # Recall
    f1_score = Column(Numeric(5, 2), nullable=True)  # F1 score

    # Human agreement metrics
    human_agreement_rate = Column(Numeric(5, 2), nullable=True)  # Agreement with humans
    false_positive_rate = Column(Numeric(5, 2), nullable=True)  # False positive violations
    false_negative_rate = Column(Numeric(5, 2), nullable=True)  # Missed violations

    # Evaluation details
    total_evaluations = Column(Integer, nullable=False)
    evaluation_period_start = Column(DateTime, nullable=False)
    evaluation_period_end = Column(DateTime, nullable=False)

    # Confidence metrics
    avg_confidence_score = Column(Numeric(5, 2), nullable=True)
    confidence_threshold = Column(Numeric(5, 2), nullable=True)  # Current threshold
    human_review_rate = Column(Numeric(5, 2), nullable=True)  # % requiring human review

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    dataset = relationship("FineTuningDataset")


