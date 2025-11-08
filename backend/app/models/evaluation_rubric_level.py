from sqlalchemy import Column, String, Integer, ForeignKey, Text, Numeric
from sqlalchemy.orm import relationship
from app.database import Base
import uuid


class EvaluationRubricLevel(Base):
    __tablename__ = "evaluation_rubric_levels"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    criteria_id = Column(String(36), ForeignKey("evaluation_criteria.id", ondelete="CASCADE"), nullable=False)
    level_name = Column(String(50), nullable=False)  # e.g., "Excellent", "Good", "Average", "Poor", "Unacceptable"
    level_order = Column(Integer, nullable=False)  # 1-5 (1 = highest, 5 = lowest)
    min_score = Column(Integer, nullable=False)  # Minimum score for this level (0-100)
    max_score = Column(Integer, nullable=False)  # Maximum score for this level (0-100)
    description = Column(Text, nullable=False)  # What constitutes this level of performance
    examples = Column(Text, nullable=True)  # Examples of behaviors/actions for this level
    
    # Relationships
    criteria = relationship("EvaluationCriteria", back_populates="rubric_levels")

