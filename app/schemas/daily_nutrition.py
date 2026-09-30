from typing import Optional
from pydantic import BaseModel, Field
from datetime import date as DateType

class DailyNutritionBase(BaseModel):
    date: DateType
    calories_consumed: float = Field(0.0, ge=0)
    protein_consumed: float = Field(0.0, ge=0)
    carbs_consumed: float = Field(0.0, ge=0)
    fats_consumed: float = Field(0.0, ge=0)
    fiber_consumed: float = Field(0.0, ge=0)
    water_intake: float = Field(0.0, ge=0, description="Water intake in liters or ml")

class DailyNutritionCreate(BaseModel):
    date: Optional[DateType] = None
    calories_consumed: Optional[float] = Field(0.0, ge=0)
    protein_consumed: Optional[float] = Field(0.0, ge=0)
    carbs_consumed: Optional[float] = Field(0.0, ge=0)
    fats_consumed: Optional[float] = Field(0.0, ge=0)
    fiber_consumed: Optional[float] = Field(0.0, ge=0)
    water_intake: Optional[float] = Field(0.0, ge=0)

class DailyNutritionResponse(DailyNutritionBase):
    id: str
    user_id: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class DailyNutritionSummary(BaseModel):
    date: DateType
    calories_consumed: float = 0.0
    calorie_target: float = 2000.0
    protein_consumed: float = 0.0
    protein_target: float = 140.0
    carbs_consumed: float = 0.0
    carbs_target: float = 225.0
    fat_consumed: float = 0.0
    fat_target: float = 65.0
    fiber_consumed: float = 0.0
    water_intake: float = 0.0
    water_target: float = 2500.0
    calorie_progress_pct: float = 0.0
    protein_progress_pct: float = 0.0
