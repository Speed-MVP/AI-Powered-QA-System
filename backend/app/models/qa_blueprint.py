"""
QA Blueprint Model - Phase 2
Master table for QA Blueprints
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Integer, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import uuid
import enum


class BlueprintStatus(str, enum.Enum):
    """Blueprint status"""
    draft = "draft"
    published = "published"
    archived = "archived"


class QABlueprint(Base):
    __tablename__ = "qa_blueprints"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(SQLEnum(BlueprintStatus), nullable=False, default=BlueprintStatus.draft, index=True)
    version_number = Column(Integer, nullable=False, default=1)
    compiled_flow_version_id = Column(String(36), nullable=True)  # FK to compiled_flow_versions (set after publish)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    updated_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    extra_metadata = Column(JSONB, nullable=True, name="metadata")  # UI hints, preset name, import source, etc.
    
    # Relationships
    company = relationship("Company", back_populates="qa_blueprints")
    stages = relationship("QABlueprintStage", back_populates="blueprint", cascade="all, delete-orphan", order_by="QABlueprintStage.ordering_index")
    versions = relationship("QABlueprintVersion", back_populates="blueprint", cascade="all, delete-orphan", order_by="QABlueprintVersion.version_number.desc()")
    audit_logs = relationship("QABlueprintAuditLog", back_populates="blueprint", cascade="all, delete-orphan", order_by="QABlueprintAuditLog.created_at.desc()")
    
    def __repr__(self):
        return f"<QABlueprint(id='{self.id}', name='{self.name}', status={self.status.value}, version={self.version_number})>"

