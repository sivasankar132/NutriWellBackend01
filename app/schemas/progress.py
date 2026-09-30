from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import date as DateType

class ProgressRecordBase(BaseModel):
    date: DateType
    weight: float = Field(..., gt=0, description="Weight in kg")
    bmi: Optional[float] = Field(None, gt=0)
    calories_consumed: Optional[float] = Field(0.0, ge=0)
    notes: Optional[str] = None

class ProgressRecordCreate(BaseModel):
    date: Optional[DateType] = None
    weight: float = Field(..., gt=0)
    bmi: Optional[float] = Field(None, gt=0)
    calories_consumed: Optional[float] = Field(0.0, ge=0)
    notes: Optional[str] = None

class ProgressRecordUpdate(BaseModel):
    date: Optional[DateType] = None
    weight: Optional[float] = Field(None, gt=0)
    bmi: Optional[float] = Field(None, gt=0)
    calories_consumed: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None

class ProgressRecordResponse(ProgressRecordBase):
    id: str
    user_id: str
    created_at: Optional[str] = None

class ProgressSummaryResponse(BaseModel):
    current_weight: Optional[float] = None
    starting_weight: Optional[float] = None
    weight_change: Optional[float] = None
    current_bmi: Optional[float] = None
    target_weight: Optional[float] = None
    total_logs: int = 0
    records: List[ProgressRecordResponse] = Field(default_factory=list)
