"""
Rule Audit Log Model
Phase 5: Structured Rule Editor UI & Admin Tools

Immutable audit trail for all rule changes.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import uuid


class RuleAuditLog(Base):
    __tablename__ = "rule_audit_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    policy_template_id = Column(String(36), ForeignKey("policy_templates.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    action = Column(String(50), nullable=False)  # create_draft, publish, rollback, etc.
    delta = Column(JSONB, nullable=True)  # Diff of changes
    reason = Column(Text, nullable=True)  # Optional reason for change
    rules_hash = Column(String(64), nullable=True)  # Hash of rules after change
    draft_id = Column(String(36), nullable=True)  # Related draft ID if applicable
    version_id = Column(String(36), nullable=True)  # Related version ID if applicable
    llm_generated = Column(Boolean, default=False)  # Whether change was LLM-generated
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    policy_template = relationship("PolicyTemplate", back_populates="rule_audit_logs")
    user = relationship("User", foreign_keys=[user_id])

