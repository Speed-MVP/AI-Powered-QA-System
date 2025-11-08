from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Numeric, Integer
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import uuid


class EvaluationCriteria(Base):
    __tablename__ = "evaluation_criteria"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    policy_template_id = Column(String(36), ForeignKey("policy_templates.id"), nullable=False)
    category_name = Column(String(255), nullable=False)
    weight = Column(Numeric(5, 2), nullable=False)  # Must sum to 100 per template
    passing_score = Column(Integer, nullable=False)  # 0-100
    evaluation_prompt = Column(Text, nullable=False)  # LLM instruction for this criteria
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    policy_template = relationship("PolicyTemplate", back_populates="evaluation_criteria")
    policy_violations = relationship("PolicyViolation", back_populates="criteria")
    rubric_levels = relationship("EvaluationRubricLevel", back_populates="criteria", cascade="all, delete-orphan", order_by="EvaluationRubricLevel.level_order")

