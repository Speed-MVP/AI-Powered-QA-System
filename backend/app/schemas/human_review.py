from pydantic import BaseModel
from typing import Dict


class HumanReviewSubmit(BaseModel):
    human_overall_score: int
    human_category_scores: Dict[str, int]
    ai_score_accuracy: float

