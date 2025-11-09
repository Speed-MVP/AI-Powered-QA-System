from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import enum
import uuid


class UserRole(str, enum.Enum):
    admin = "admin"
    qa_manager = "qa_manager"
    reviewer = "reviewer"


class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # NULL if using OAuth
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.reviewer)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    company = relationship("Company", back_populates="users")
    recordings = relationship("Recording", back_populates="uploaded_by_user")
    evaluations = relationship("Evaluation", back_populates="evaluated_by_user")
    human_reviews = relationship("HumanReview", back_populates="reviewer", cascade="all, delete-orphan")  # Phase 3

