"""
Phase 2: Policy Rule Builder - Policy Rules Draft Model
Stores drafts during the rule generation and clarification process.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, Boolean, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import enum
import uuid


class DraftStatus(str, enum.Enum):
    generating = "generating"
    needs_clarification = "needs_clarification"
    ready_for_confirm = "ready_for_confirm"
    validation_failed = "validation_failed"
    confirmed = "confirmed"
    failed = "failed"


class PolicyRulesDraft(Base):
    __tablename__ = "policy_rules_drafts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    policy_template_id = Column(String(36), ForeignKey("policy_templates.id"), nullable=False)
    status = Column(Enum(DraftStatus), nullable=False, default=DraftStatus.generating)

    # Input data
    policy_text = Column(Text, nullable=False)
    rubric_levels = Column(JSONB, nullable=True)  # Rubric metadata from policy template
    examples = Column(Text, nullable=True)        # Optional example calls

    # Generated content
    generated_rules = Column(JSONB, nullable=True)    # LLM-generated policy_rules JSON
    clarifications = Column(JSONB, nullable=True)     # List of clarification questions from LLM
    user_answers = Column(JSONB, nullable=True)       # User's answers to clarifications

    # Phase 5: Rule Editor UI enhancements
    name = Column(String(100), nullable=True)         # Human-readable draft name
    description = Column(Text, nullable=True)         # Draft description/notes
    parent_version = Column(Integer, nullable=True)   # Version this draft was created from
    is_manual_edit = Column(Boolean, nullable=False, default=False)  # True if draft contains manual edits
    last_edited_by_user_id = Column(String(36), ForeignKey("users.id"), nullable=True)

    # Metadata and debugging
    llm_raw_response = Column(Text, nullable=True)    # Raw LLM response for debugging
    validation_errors = Column(JSONB, nullable=True)  # Validation errors if any

    # LLM metrics
    llm_model = Column(String(100), nullable=True)
    llm_tokens_used = Column(Integer, nullable=True)
    llm_latency_ms = Column(Integer, nullable=True)
    llm_prompt_hash = Column(String(64), nullable=True)  # SHA-256 hash of prompt used

    # Audit fields
    created_by_user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False, onupdate=datetime.utcnow)

    # Relationships
    policy_template = relationship("PolicyTemplate", back_populates="policy_rules_drafts")
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])
    last_edited_by_user = relationship("User", foreign_keys=[last_edited_by_user_id])

    def __repr__(self):
        return f"<PolicyRulesDraft(id='{self.id}', template_id='{self.policy_template_id}', status='{self.status}')>"
