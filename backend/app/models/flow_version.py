"""
Phase 1: FlowVersion Model
Represents a versioned SOP (Standard Operating Procedure) structure with Stages and Steps.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Integer, Text
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import uuid


class FlowVersion(Base):
    __tablename__ = "flow_versions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    version_number = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    company = relationship("Company", back_populates="flow_versions")
    stages = relationship("FlowStage", back_populates="flow_version", cascade="all, delete-orphan", order_by="FlowStage.order")
    compliance_rules = relationship("ComplianceRule", back_populates="flow_version", cascade="all, delete-orphan")
    rubric_templates = relationship("RubricTemplate", back_populates="flow_version", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<FlowVersion(id='{self.id}', name='{self.name}', version={self.version_number})>"

