from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum


class ReviewStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"


class HumanReviewCreate(BaseModel):
    reviewer_notes: Optional[str] = None
    human_scores: Dict[str, float]  # Overall and category scores
    overall_score: Optional[float] = None  # For backward compatibility
    human_violations: Optional[List[Dict]] = None  # Human-identified violations
    corrections: Optional[Dict] = None  # AI score corrections


class HumanReviewQueueItem(BaseModel):
    evaluation_id: str
    recording_id: str
    recording_title: str
    ai_overall_score: float
    ai_category_scores: Dict[str, float]
    ai_violations: List[Dict]
    rule_engine_results: Dict
    confidence_score: float
    transcript_preview: str
    created_at: datetime


class HumanReviewResponse(BaseModel):
    id: str
    evaluation_id: str
    reviewer_user_id: str
    human_overall_score: Optional[float]
    human_category_scores: Optional[Dict[str, float]]
    human_violations: Optional[List[Dict]]
    ai_scores: Optional[Dict]  # Snapshot of AI scores
    delta: Optional[Dict]  # Computed differences
    reviewer_notes: Optional[str]
    status: ReviewStatus
    created_at: datetime

    class Config:
        from_attributes = True

