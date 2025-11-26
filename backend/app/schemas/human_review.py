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
    human_stage_scores: List[Dict]  # Stage scores with stage_id and score
    human_overall_score: Optional[float] = None
    human_violations: Optional[List[Dict]] = None  # Human-identified violations
    corrections: Optional[Dict] = None  # AI score corrections


class HumanReviewQueueItem(BaseModel):
    evaluation_id: str
    recording_id: str
    recording_title: str
    ai_overall_score: float
    ai_stage_scores: List[Dict]
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
    human_stage_scores: Optional[List[Dict]]
    human_violations: Optional[List[Dict]]
    ai_scores: Optional[Dict]  # Snapshot of AI scores
    delta: Optional[Dict]  # Computed differences
    reviewer_notes: Optional[str]
    status: ReviewStatus
    created_at: datetime

    class Config:
        from_attributes = True

