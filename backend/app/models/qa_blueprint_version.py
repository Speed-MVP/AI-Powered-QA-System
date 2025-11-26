"""
QA Blueprint Version Model - Phase 2
Published snapshots (immutable)
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import uuid


class QABlueprintVersion(Base):
    __tablename__ = "qa_blueprint_versions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    blueprint_id = Column(String(36), ForeignKey("qa_blueprints.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    snapshot = Column(JSONB, nullable=False)  # full blueprint JSON (stages + behaviors + metadata)
    compiled_flow_version_id = Column(String(36), nullable=True)  # created by compiler
    published_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    published_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    blueprint = relationship("QABlueprint", back_populates="versions")
    compiler_maps = relationship("QABlueprintCompilerMap", back_populates="blueprint_version", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<QABlueprintVersion(id='{self.id}', blueprint_id='{self.blueprint_id}', version={self.version_number})>"

