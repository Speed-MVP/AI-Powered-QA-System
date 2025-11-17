"""
Rule Version Model
Phase 5: Structured Rule Editor UI & Admin Tools

Immutable version snapshots of published rules.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import uuid


class RuleVersion(Base):
    __tablename__ = "rule_versions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    policy_template_id = Column(String(36), ForeignKey("policy_templates.id"), nullable=False)
    rules_json = Column(JSONB, nullable=False)  # Immutable rules snapshot
    rules_hash = Column(String(64), nullable=False)  # SHA256 hash
    rules_version = Column(Integer, nullable=False)  # Sequential version number
    created_by_user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    llm_generated_flag = Column(Boolean, default=False)  # Whether rules were AI-generated
    
    # Relationships
    policy_template = relationship("PolicyTemplate", back_populates="rule_versions")
    created_by = relationship("User", foreign_keys=[created_by_user_id])

