"""
Phase 1: FlowStep Model
Represents a step within a FlowStage (e.g., Greet customer, Verify identity).
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import uuid


class FlowStep(Base):
    __tablename__ = "flow_steps"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    stage_id = Column(String(36), ForeignKey("flow_stages.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)  # Allow NULL or empty string
    required = Column(Boolean, default=False, nullable=False)
    expected_phrases = Column(JSONB, nullable=True)  # Array of strings
    timing_requirement = Column(JSONB, nullable=True)  # {enabled: bool, seconds: number}
    order = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    stage = relationship("FlowStage", back_populates="steps")
    
    def __repr__(self):
        return f"<FlowStep(id='{self.id}', name='{self.name}', required={self.required}, order={self.order})>"

