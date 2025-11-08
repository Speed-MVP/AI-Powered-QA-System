from sqlalchemy import Column, String, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from app.database import Base
import enum
import uuid


class ViolationSeverity(str, enum.Enum):
    critical = "critical"
    major = "major"
    minor = "minor"


class PolicyViolation(Base):
    __tablename__ = "policy_violations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    evaluation_id = Column(String(36), ForeignKey("evaluations.id"), nullable=False)
    criteria_id = Column(String(36), ForeignKey("evaluation_criteria.id"), nullable=False)
    violation_type = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(Enum(ViolationSeverity), nullable=False)
    
    # Relationships
    evaluation = relationship("Evaluation", back_populates="policy_violations")
    criteria = relationship("EvaluationCriteria", back_populates="policy_violations")

