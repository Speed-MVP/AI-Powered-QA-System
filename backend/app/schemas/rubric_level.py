from pydantic import BaseModel
from typing import Optional
from decimal import Decimal


class RubricLevelCreate(BaseModel):
    level_name: str
    level_order: int
    min_score: int
    max_score: int
    description: str
    examples: Optional[str] = None


class RubricLevelResponse(BaseModel):
    id: str
    criteria_id: str
    level_name: str
    level_order: int
    min_score: int
    max_score: int
    description: str
    examples: Optional[str] = None
    
    class Config:
        from_attributes = True

