from typing import Optional, List, Literal, Union, Any
from pydantic import BaseModel, Field, model_validator
from datetime import date as DateType

MealType = Literal["breakfast", "lunch", "dinner", "snack", "Breakfast", "Lunch", "Dinner", "Snacks"]

class MealItemBase(BaseModel):
    food_id: Optional[str] = None
    food_name: str = Field(..., min_length=1)
    quantity: float = Field(1.0, gt=0)
    serving_size: Union[str, float, int] = "1 serving"
    calories: float = Field(..., ge=0)
    protein: float = Field(0.0, ge=0)
    carbs: float = Field(0.0, ge=0)
    fats: float = Field(0.0, ge=0)
    fiber: Optional[float] = Field(0.0, ge=0)
    cost_inr: Optional[float] = Field(0.0, ge=0)

    @model_validator(mode='before')
    @classmethod
    def normalize_meal_item_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "protein_g" in data and "protein" not in data:
                data["protein"] = data["protein_g"]
            if "carbs_g" in data and "carbs" not in data:
                data["carbs"] = data["carbs_g"]
            if "fat_g" in data and "fats" not in data:
                data["fats"] = data["fat_g"]
            if "fats_g" in data and "fats" not in data:
                data["fats"] = data["fats_g"]
            if "fiber_g" in data and "fiber" not in data:
                data["fiber"] = data["fiber_g"]
            if "serving_size" in data and isinstance(data["serving_size"], (int, float)):
                unit = data.get("serving_unit", "serving")
                data["serving_size"] = f"{data['serving_size']} {unit}"
        return data

class MealItemCreate(MealItemBase):
    pass

class MealItemUpdate(BaseModel):
    food_name: Optional[str] = None
    quantity: Optional[float] = Field(None, gt=0)
    serving_size: Optional[Union[str, float, int]] = None
    calories: Optional[float] = Field(None, ge=0)
    protein: Optional[float] = Field(None, ge=0)
    carbs: Optional[float] = Field(None, ge=0)
    fats: Optional[float] = Field(None, ge=0)
    fiber: Optional[float] = Field(None, ge=0)
    cost_inr: Optional[float] = Field(None, ge=0)

class MealItemResponse(MealItemBase):
    id: str
    meal_id: str
    created_at: Optional[str] = None

class MealBase(BaseModel):
    meal_type: MealType = Field(..., description="breakfast, lunch, dinner, snack")
    meal_date: Optional[DateType] = None
    notes: Optional[str] = None

    @model_validator(mode='before')
    @classmethod
    def normalize_meal_base_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "date" in data and "meal_date" not in data:
                data["meal_date"] = data["date"]
            if "name" in data and "notes" not in data:
                data["notes"] = data["name"]
        return data

class MealCreate(MealBase):
    items: List[MealItemCreate] = Field(default_factory=list)
    total_calories: Optional[float] = None
    total_protein_g: Optional[float] = None
    total_carbs_g: Optional[float] = None
    total_fat_g: Optional[float] = None

class MealUpdate(BaseModel):
    meal_type: Optional[MealType] = None
    meal_date: Optional[DateType] = None
    notes: Optional[str] = None

class MealResponse(MealBase):
    id: str
    user_id: str
    total_calories: float = 0.0
    total_protein: float = 0.0
    total_carbs: float = 0.0
    total_fats: float = 0.0
    total_fiber: float = 0.0
    items: List[MealItemResponse] = Field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
