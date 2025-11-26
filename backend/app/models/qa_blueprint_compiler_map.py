"""
QA Blueprint Compiler Map Model - Phase 2
Mapping to internal artifacts for traceability
"""

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import uuid


class QABlueprintCompilerMap(Base):
    __tablename__ = "qa_blueprint_compiler_map"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    blueprint_version_id = Column(String(36), ForeignKey("qa_blueprint_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    flow_version_id = Column(String(36), nullable=True)  # FK to compiled_flow_versions
    policy_rules_version_id = Column(String(36), nullable=True)  # FK to policy_rules_versions (if generated)
    rubric_template_id = Column(String(36), nullable=True)  # FK to compiled_rubric_templates
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    blueprint_version = relationship("QABlueprintVersion", back_populates="compiler_maps")
    
    def __repr__(self):
        return f"<QABlueprintCompilerMap(id='{self.id}', blueprint_version_id='{self.blueprint_version_id}')>"

