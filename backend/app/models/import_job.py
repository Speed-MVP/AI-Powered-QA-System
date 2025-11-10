from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import uuid


class ImportJob(Base):
    __tablename__ = "import_jobs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False, index=True)
    source_type = Column(String(50), nullable=False)  # 'csv', 'api', 'manual_ui', 'webhook'
    source_platform = Column(String(50), default="n/a", nullable=True)  # 'n/a', 'genesys', 'five9', etc.
    status = Column(String(50), default="pending", nullable=False, index=True)  # 'pending', 'processing', 'completed', 'failed'
    file_name = Column(String(255), nullable=True)
    rows_total = Column(Integer, nullable=True)
    rows_processed = Column(Integer, default=0, nullable=True)
    rows_failed = Column(Integer, default=0, nullable=True)
    validation_errors = Column(JSONB, nullable=True)  # Array of error objects
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    company = relationship("Company")
    created_by_user = relationship("User", foreign_keys=[created_by])


