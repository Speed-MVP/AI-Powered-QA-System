"""
QA Blueprint Audit Log Model - Phase 2
Per-change audit trail
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import uuid
import enum


class ChangeType(str, enum.Enum):
    """Change type"""
    create = "create"
    update = "update"
    delete = "delete"
    publish = "publish"


class QABlueprintAuditLog(Base):
    __tablename__ = "qa_blueprint_audit_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    blueprint_id = Column(String(36), ForeignKey("qa_blueprints.id", ondelete="CASCADE"), nullable=False, index=True)
    changed_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    change_type = Column(SQLEnum(ChangeType), nullable=False)
    change_summary = Column(Text, nullable=True)  # short human notes
    change_diff = Column(JSONB, nullable=True)  # optional diff patch
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    blueprint = relationship("QABlueprint", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<QABlueprintAuditLog(id='{self.id}', blueprint_id='{self.blueprint_id}', change_type={self.change_type.value})>"

