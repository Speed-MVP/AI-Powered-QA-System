from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import uuid


class PolicyTemplate(Base):
    __tablename__ = "policy_templates"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    template_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Phase 1: Structured Rules Foundation
    policy_rules = Column(JSONB, nullable=True)  # Structured machine-readable rules
    policy_rules_version = Column(Integer, nullable=True)  # Version number for rules
    rules_generated_at = Column(DateTime, nullable=True)  # When rules were generated
    rules_approved_by_user_id = Column(String(36), ForeignKey("users.id"), nullable=True)  # Who approved rules
    rules_generation_method = Column(String(20), nullable=True)  # 'ai', 'manual', or null
    enable_structured_rules = Column(Boolean, default=False)  # Feature flag for structured rules
    
    # Relationships
    company = relationship("Company", back_populates="policy_templates")
    evaluation_criteria = relationship("EvaluationCriteria", back_populates="policy_template", cascade="all, delete-orphan")
    evaluations = relationship("Evaluation", back_populates="policy_template")
    clarifications = relationship("PolicyClarification", back_populates="policy_template", cascade="all, delete-orphan")
    rule_drafts = relationship("RuleDraft", back_populates="policy_template", cascade="all, delete-orphan")
    rule_versions = relationship("RuleVersion", back_populates="policy_template", cascade="all, delete-orphan")
    rule_audit_logs = relationship("RuleAuditLog", back_populates="policy_template", cascade="all, delete-orphan")

