"""
QA Blueprint Stage Model - Phase 2
Ordered stages per blueprint
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import uuid


class QABlueprintStage(Base):
    __tablename__ = "qa_blueprint_stages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    blueprint_id = Column(String(36), ForeignKey("qa_blueprints.id", ondelete="CASCADE"), nullable=False, index=True)
    stage_name = Column(String(150), nullable=False)
    ordering_index = Column(Integer, nullable=False)  # 1..N; used for UI order
    stage_weight = Column(Numeric(5, 2), nullable=True)  # percent of total (0-100); optional (system can auto-calc)
    extra_metadata = Column(JSONB, nullable=True, name="metadata")  # collapsed UI hint, sample transcript window length, stage color, etc.
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    blueprint = relationship("QABlueprint", back_populates="stages")
    behaviors = relationship("QABlueprintBehavior", back_populates="stage", cascade="all, delete-orphan", order_by="QABlueprintBehavior.ui_order")
    
    def __repr__(self):
        return f"<QABlueprintStage(id='{self.id}', stage_name='{self.stage_name}', ordering_index={self.ordering_index}, weight={self.stage_weight})>"

