from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import uuid


class Transcript(Base):
    __tablename__ = "transcripts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recording_id = Column(String(36), ForeignKey("recordings.id"), nullable=False, unique=True)
    transcript_text = Column(Text, nullable=False)
    diarized_segments = Column(JSONB, nullable=True)  # [{speaker: "agent"|"customer", text: "", timestamp: 0.0}, ...]
    sentiment_analysis = Column(JSONB, nullable=True)  # Voice-based sentiment analysis from Deepgram
    transcription_confidence = Column(Numeric(5, 2), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    recording = relationship("Recording", back_populates="transcript")

