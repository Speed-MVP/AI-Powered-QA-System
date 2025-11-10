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
    # Phase 1: Audit fields
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    updated_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    company = relationship("Company", back_populates="users")
    recordings = relationship("Recording", foreign_keys="Recording.uploaded_by_user_id", back_populates="uploaded_by_user")
    evaluations = relationship("Evaluation", foreign_keys="Evaluation.evaluated_by_user_id", back_populates="evaluated_by_user")
    human_reviews = relationship("HumanReview", back_populates="reviewer", cascade="all, delete-orphan")  # Phase 3
    # Phase 1: Agent/Team relationships
    team_memberships = relationship("AgentTeamMembership", foreign_keys="AgentTeamMembership.agent_id", back_populates="agent")
    created_teams = relationship("Team", foreign_keys="Team.created_by", back_populates="created_by_user")
    updated_teams = relationship("Team", foreign_keys="Team.updated_by", back_populates="updated_by_user")

