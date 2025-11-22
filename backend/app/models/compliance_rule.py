"""
Phase 2: ComplianceRule Model
Represents compliance rules tied to a FlowVersion.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import uuid
import enum


class RuleType(str, enum.Enum):
    """Compliance rule types per Phase 2 spec"""
    required_phrase = "required_phrase"
    forbidden_phrase = "forbidden_phrase"
    sequence_rule = "sequence_rule"
    timing_rule = "timing_rule"
    verification_rule = "verification_rule"
    conditional_rule = "conditional_rule"


class Severity(str, enum.Enum):
    """Rule severity levels"""
    critical = "critical"
    major = "major"
    minor = "minor"


class ComplianceRule(Base):
    __tablename__ = "compliance_rules"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    flow_version_id = Column(String(36), ForeignKey("flow_versions.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(SQLEnum(Severity), nullable=False)
    rule_type = Column(SQLEnum(RuleType), nullable=False)
    applies_to_stages = Column(JSONB, nullable=True)  # Array of stage_ids, empty = whole call
    params = Column(JSONB, nullable=False)  # Rule type-specific parameters
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    flow_version = relationship("FlowVersion", back_populates="compliance_rules")
    
    def __repr__(self):
        return f"<ComplianceRule(id='{self.id}', title='{self.title}', rule_type={self.rule_type.value}, severity={self.severity.value})>"

