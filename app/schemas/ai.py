from typing import Optional, List, Dict, Any, Generic, TypeVar, Union
from pydantic import BaseModel, Field, ConfigDict

T = TypeVar("T")

class AISuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T

class AIErrorResponse(BaseModel):
    success: bool = False
    error_code: str
    message: str = "AI generation failed. Please try again."

class AIChatResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    sender: str = "ai"
    text: str
    timestamp: str
    recommended_meal: Optional[Union[Dict[str, Any], str]] = Field(default=None, alias="recommendedMeal")

class AIScanFoodResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    name: str
    serving: str
    diet_type: str = Field(default="Veg", alias="dietType")
    calories: float
    protein: float
    carbs: float
    fat: float
    fiber: float
    vitamins: List[str] = Field(default_factory=list)
    minerals: List[str] = Field(default_factory=list)
    cost_inr: float = Field(default=50.0, alias="costInr")
    confidence_score: float = Field(default=90.0, alias="confidenceScore")
    health_rating: str = Field(default="Good", alias="healthRating")
    ai_advice: str = Field(default="", alias="aiAdvice")

class WhatShouldIEatOption(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    title: str
    category: str
    calories: float
    protein: float
    cost_inr: float = Field(..., alias="costInr")
    prep_time_minutes: int = Field(..., alias="prepTimeMinutes")
    reason_why: str = Field(..., alias="reasonWhy")
    food_item: Optional[Union[Dict[str, Any], str]] = Field(default=None, alias="foodItem")

class AIWhatShouldIEatResult(BaseModel):
    options: List[WhatShouldIEatOption]

class AIBadDayRecoveryResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    empathetic_headline: str = Field(..., alias="empatheticHeadline")
    advice_message: str = Field(..., alias="adviceMessage")
    suggested_evening_action: str = Field(..., alias="suggestedEveningAction")
    recommended_recovery_meal: Optional[Union[Dict[str, Any], str]] = Field(default=None, alias="recommendedRecoveryMeal")

class AIIfIEatThisResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    food_name: str = Field(..., alias="foodName")
    calories: float
    protein: float
    carbs: float
    fat: float
    fiber: float
    cost_inr: float = Field(..., alias="costInr")
    projected_calorie_pct: float = Field(..., alias="projectedCaloriePct")
    projected_protein_pct: float = Field(..., alias="projectedProteinPct")
    better_swap: Optional[Union[Dict[str, Any], str]] = Field(default=None, alias="betterSwap")
    ai_advice: str = Field(..., alias="aiAdvice")
