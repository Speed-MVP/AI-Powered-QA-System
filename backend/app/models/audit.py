"""
Audit and Compliance Models
Phase 4: Scale & Optimization
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Numeric, Integer, Boolean, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import enum
import uuid


class AuditEventType(str, enum.Enum):
    evaluation_created = "evaluation_created"
    evaluation_updated = "evaluation_updated"
    evaluation_reviewed = "evaluation_reviewed"
    evaluation_overridden = "evaluation_overridden"
    model_changed = "model_changed"
    policy_updated = "policy_updated"
    batch_processed = "batch_processed"


class AuditLog(Base):
    """
    Comprehensive audit trail for all QA system activities.
    Phase 4: Store all evaluations and policies with version control.
    """
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = Column(Enum(AuditEventType), nullable=False)
    entity_type = Column(String(50), nullable=False)  # "evaluation", "recording", "model", etc.
    entity_id = Column(String(36), nullable=False)

    # User who performed the action
    user_id = Column(String(36), nullable=True)
    user_role = Column(String(50), nullable=True)

    # Before/after state for change tracking
    old_values = Column(JSONB, nullable=True)
    new_values = Column(JSONB, nullable=True)

    # Event metadata
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)

    # Event details
    action = Column(String(100), nullable=False)  # "created", "updated", "deleted", etc.
    description = Column(Text, nullable=True)
    reason = Column(Text, nullable=True)  # Why the action was taken

    # Compliance metadata
    model_version = Column(String(50), nullable=True)  # Which AI model was used
    confidence_score = Column(Numeric(5, 2), nullable=True)  # AI confidence at time of event
    compliance_flags = Column(JSONB, nullable=True)  # Regulatory compliance markers

    created_at = Column(DateTime, default=datetime.utcnow)


class EvaluationVersion(Base):
    """
    Version control for evaluations to track changes over time.
    Phase 4: Include model version, timestamp, and reasoning snippet for audit defense.
    """
    __tablename__ = "evaluation_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    evaluation_id = Column(String(36), ForeignKey("evaluations.id"), nullable=False, index=True)

    # Version metadata
    version_number = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    created_by = Column(String(36), nullable=True)  # User who created this version

    # Complete evaluation state at this version
    overall_score = Column(Integer, nullable=False)
    confidence_score = Column(Numeric(5, 2), nullable=True)
    category_scores = Column(JSONB, nullable=False)
    violations = Column(JSONB, nullable=True)
    llm_analysis = Column(JSONB, nullable=True)

    # Model and processing metadata
    model_used = Column(String(50), nullable=True)
    model_version = Column(String(50), nullable=True)
    processing_pipeline_version = Column(String(20), nullable=True)  # e.g., "v2.1.3"

    # Audit trail
    change_reason = Column(Text, nullable=True)  # Why this version was created
    previous_version_id = Column(String(36), nullable=True)

    # Compliance and regulatory
    regulatory_compliance = Column(JSONB, nullable=True)  # Compliance requirements met
    audit_trail_hash = Column(String(64), nullable=True)  # Cryptographic hash for tamper detection

    # Relationships
    evaluation = relationship("Evaluation", back_populates="versions")


class ComplianceReport(Base):
    """
    Automated compliance reports for regulatory requirements.
    Phase 4: Store evaluations with version control for audit defense.
    """
    __tablename__ = "compliance_reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Report metadata
    report_type = Column(String(50), nullable=False)  # "monthly", "quarterly", "annual"
    report_period_start = Column(DateTime, nullable=False)
    report_period_end = Column(DateTime, nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)

    # Compliance metrics
    total_evaluations = Column(Integer, default=0)
    human_review_rate = Column(Numeric(5, 2), nullable=True)
    average_confidence = Column(Numeric(5, 2), nullable=True)
    model_accuracy_score = Column(Numeric(5, 2), nullable=True)

    # Regulatory compliance flags
    gdpr_compliant = Column(Boolean, default=True)
    hipaa_compliant = Column(Boolean, default=True)
    sox_compliant = Column(Boolean, default=True)

    # Quality metrics
    false_positive_rate = Column(Numeric(5, 2), nullable=True)
    false_negative_rate = Column(Numeric(5, 2), nullable=True)
    human_agreement_rate = Column(Numeric(5, 2), nullable=True)

    # Report data
    evaluation_summary = Column(JSONB, nullable=True)
    violation_breakdown = Column(JSONB, nullable=True)
    model_performance = Column(JSONB, nullable=True)

    # Approval workflow
    status = Column(String(20), default="draft")  # "draft", "reviewed", "approved", "archived"
    reviewed_by = Column(String(36), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    approved_by = Column(String(36), nullable=True)
    approved_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class DataRetentionPolicy(Base):
    """
    Data retention policies for compliance.
    """
    __tablename__ = "data_retention_policies"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_type = Column(String(50), nullable=False)  # "evaluation", "recording", "audit_log"

    # Retention rules
    retention_period_days = Column(Integer, nullable=False)
    retention_reason = Column(Text, nullable=True)

    # GDPR compliance
    data_categories = Column(JSONB, nullable=True)  # ["personal_data", "audio_recording", etc.]
    legal_basis = Column(String(100), nullable=True)  # "consent", "contract", "legitimate_interest"

    # Automation
    auto_delete = Column(Boolean, default=True)
    deletion_method = Column(String(20), default="anonymize")  # "delete", "anonymize", "archive"

    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
