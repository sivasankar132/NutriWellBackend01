from typing import Optional, Literal, Union, Any
from pydantic import BaseModel, Field

GoalType = Literal["weight_loss", "weight_gain", "maintenance", "muscle_gain", "healthy_eating"]

class NutritionGoalBase(BaseModel):
    goal_type: GoalType = Field("maintenance", description="Target health goal")
    target_weight: Optional[float] = Field(None, gt=0, description="Target weight in kg")
    daily_calorie_target: float = Field(..., gt=0)
    daily_protein_target: float = Field(..., ge=0)
    daily_carbs_target: float = Field(..., ge=0)
    daily_fat_target: float = Field(..., ge=0)

class NutritionGoalCreate(BaseModel):
    goal_type: GoalType = Field("maintenance")
    target_weight: Optional[float] = Field(None, gt=0)
    daily_calorie_target: Optional[float] = Field(None, gt=0)
    daily_protein_target: Optional[float] = Field(None, ge=0)
    daily_carbs_target: Optional[float] = Field(None, ge=0)
    daily_fat_target: Optional[float] = Field(None, ge=0)

class NutritionGoalUpdate(BaseModel):
    goal_type: Optional[GoalType] = None
    target_weight: Optional[float] = None
    daily_calorie_target: Optional[float] = None
    daily_protein_target: Optional[float] = None
    daily_carbs_target: Optional[float] = None
    daily_fat_target: Optional[float] = None

class NutritionGoalResponse(NutritionGoalBase):
    id: Union[str, Any]
    user_id: Union[str, Any]
    created_at: Optional[Union[str, Any]] = None
    updated_at: Optional[Union[str, Any]] = None
