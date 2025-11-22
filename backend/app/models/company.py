from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import uuid


class Company(Base):
    __tablename__ = "companies"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_name = Column(String(255), nullable=False)
    industry = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    users = relationship("User", back_populates="company")
    recordings = relationship("Recording", back_populates="company")
    teams = relationship("Team", back_populates="company")
    flow_versions = relationship("FlowVersion", back_populates="company")

