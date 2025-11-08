from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import uuid


class PolicyTemplate(Base):
    __tablename__ = "policy_templates"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    template_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    company = relationship("Company", back_populates="policy_templates")
    evaluation_criteria = relationship("EvaluationCriteria", back_populates="policy_template", cascade="all, delete-orphan")
    evaluations = relationship("Evaluation", back_populates="policy_template")

