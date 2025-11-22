"""
Phase 5: Rubric Template Models
Rubric system linked to FlowVersion stages/steps.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Integer, Text, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import uuid


class RubricTemplate(Base):
    __tablename__ = "rubric_templates"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    flow_version_id = Column(String(36), ForeignKey("flow_versions.id", ondelete="CASCADE"), nullable=False)
    version_number = Column(Integer, nullable=False, default=1)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=False, nullable=False)
    created_by_user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    flow_version = relationship("FlowVersion", back_populates="rubric_templates")
    categories = relationship("RubricCategory", back_populates="rubric_template", cascade="all, delete-orphan", order_by="RubricCategory.id")
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])
    
    def __repr__(self):
        return f"<RubricTemplate(id='{self.id}', name='{self.name}', version={self.version_number})>"


class RubricCategory(Base):
    __tablename__ = "rubric_categories"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rubric_template_id = Column(String(36), ForeignKey("rubric_templates.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    weight = Column(Numeric(5, 2), nullable=False)  # Percentage, must sum to 100
    pass_threshold = Column(Integer, nullable=False, default=75)  # 0-100
    level_definitions = Column(JSONB, nullable=True)  # Array of {name, min_score, max_score, label}
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    rubric_template = relationship("RubricTemplate", back_populates="categories")
    mappings = relationship("RubricMapping", back_populates="category", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<RubricCategory(id='{self.id}', name='{self.name}', weight={self.weight})>"


class RubricMapping(Base):
    __tablename__ = "rubric_mappings"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rubric_category_id = Column(String(36), ForeignKey("rubric_categories.id", ondelete="CASCADE"), nullable=False)
    target_type = Column(String(20), nullable=False)  # "stage" | "step"
    target_id = Column(String(36), nullable=False)  # stage_id or step_id
    contribution_weight = Column(Numeric(5, 2), nullable=False, default=1.0)  # Relative weight within category
    required_flag = Column(Boolean, default=False, nullable=False)  # If true, failing this is critical to category
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    category = relationship("RubricCategory", back_populates="mappings")
    
    def __repr__(self):
        return f"<RubricMapping(id='{self.id}', target_type='{self.target_type}', target_id='{self.target_id}')>"

