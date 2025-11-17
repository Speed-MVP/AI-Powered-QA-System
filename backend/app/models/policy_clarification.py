"""
Policy Clarification Model
Phase 2: AI Policy Rule Builder

Stores clarifying questions and answers for policy rule generation workflow.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean, JSON
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import uuid


class PolicyClarification(Base):
    __tablename__ = "policy_clarifications"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    policy_template_id = Column(String(36), ForeignKey("policy_templates.id"), nullable=False)
    question_id = Column(String(100), nullable=False)  # e.g., "q1", "q2"
    question = Column(Text, nullable=False)  # The clarification question
    answer = Column(Text, nullable=True)  # Admin's answer (null if not answered)
    answered_by_user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    answered_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="pending")  # pending, answered, approved
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    policy_template = relationship("PolicyTemplate", back_populates="clarifications")
    answered_by = relationship("User", foreign_keys=[answered_by_user_id])

