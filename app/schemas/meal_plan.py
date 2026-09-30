from typing import Optional, List, Literal
from pydantic import BaseModel, Field
from datetime import date as DateType

MealType = Literal["breakfast", "lunch", "dinner", "snack", "Breakfast", "Lunch", "Dinner", "Snacks"]

class MealPlanItemBase(BaseModel):
    food_id: Optional[str] = None
    food_name: str = Field(..., min_length=1)
    meal_type: MealType
    quantity: float = Field(1.0, gt=0)
    day_number: int = Field(1, ge=1, le=31)
    calories: float = Field(0.0, ge=0)
    protein: float = Field(0.0, ge=0)
    carbs: float = Field(0.0, ge=0)
    fats: float = Field(0.0, ge=0)

class MealPlanItemCreate(MealPlanItemBase):
    pass

class MealPlanItemResponse(MealPlanItemBase):
    id: str
    meal_plan_id: str
    created_at: Optional[str] = None

class MealPlanBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    start_date: Optional[DateType] = None
    end_date: Optional[DateType] = None

class MealPlanCreate(MealPlanBase):
    items: List[MealPlanItemCreate] = Field(default_factory=list)

class MealPlanUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[DateType] = None
    end_date: Optional[DateType] = None

class MealPlanResponse(MealPlanBase):
    id: str
    user_id: str
    items: List[MealPlanItemResponse] = Field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
