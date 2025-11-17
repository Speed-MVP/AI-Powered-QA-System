"""
Rule Draft Model
Phase 5: Structured Rule Editor UI & Admin Tools

Stores draft rules before publishing.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import uuid
import enum


class DraftStatus(str, enum.Enum):
    """Draft status values."""
    editing = "editing"
    needs_clarification = "needs_clarification"
    ready_for_confirm = "ready_for_confirm"
    validation_failed = "validation_failed"
    failed = "failed"


class RuleDraft(Base):
    __tablename__ = "rule_drafts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    policy_template_id = Column(String(36), ForeignKey("policy_templates.id"), nullable=False)
    rules_json = Column(JSONB, nullable=False)  # Draft rules
    status = Column(SQLEnum(DraftStatus), default=DraftStatus.editing)
    created_by_user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    policy_template = relationship("PolicyTemplate", back_populates="rule_drafts")
    created_by = relationship("User", foreign_keys=[created_by_user_id])

