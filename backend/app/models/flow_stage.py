"""
Phase 1: FlowStage Model
Represents a stage within a FlowVersion (e.g., Opening, Discovery, Resolution, Closing).
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import uuid


class FlowStage(Base):
    __tablename__ = "flow_stages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    flow_version_id = Column(String(36), ForeignKey("flow_versions.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    order = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    flow_version = relationship("FlowVersion", back_populates="stages")
    steps = relationship("FlowStep", back_populates="stage", cascade="all, delete-orphan", order_by="FlowStep.order")
    
    def __repr__(self):
        return f"<FlowStage(id='{self.id}', name='{self.name}', order={self.order})>"

