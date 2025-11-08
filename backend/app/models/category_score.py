from sqlalchemy import Column, String, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base
import uuid


class CategoryScore(Base):
    __tablename__ = "category_scores"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    evaluation_id = Column(String(36), ForeignKey("evaluations.id"), nullable=False)
    category_name = Column(String(255), nullable=False)
    score = Column(Integer, nullable=False)  # 0-100
    feedback = Column(Text, nullable=True)
    
    # Relationships
    evaluation = relationship("Evaluation", back_populates="category_scores")

