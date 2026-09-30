from typing import Optional, List, Literal, Any
from pydantic import BaseModel, Field, model_validator

ActivityLevelType = Literal["Sedentary", "Lightly Active", "Moderately Active", "Very Active", "Extra Active"]
DietPreferenceType = Literal["Veg", "Non-Veg", "Eggetarian", "Vegan", "Other"]
GenderType = Literal["Male", "Female", "Other"]
NutritionGoalType = Literal["weight_loss", "weight_gain", "maintenance", "muscle_gain", "healthy_eating"]

class ProfileBase(BaseModel):
    age: Optional[int] = Field(None, ge=1, le=120, description="Age in years (1 - 120)")
    gender: Optional[str] = Field(None, description="Male, Female, or Other")
    height: Optional[float] = Field(None, gt=0, le=300, description="Height in cm (e.g. 175.5)")
    weight: Optional[float] = Field(None, gt=0, le=500, description="Weight in kg (e.g. 70.0)")
    activity_level: Optional[str] = Field("Moderately Active", description="Sedentary, Lightly Active, Moderately Active, Very Active")
    dietary_preference: Optional[str] = Field("Veg", description="Veg, Non-Veg, Eggetarian, Vegan")
    food_preferences: Optional[List[str]] = Field(default_factory=list, description="Preferred cuisines or dishes")
    allergies: Optional[List[str]] = Field(default_factory=list, description="Allergies e.g. Peanuts, Dairy, Gluten")
    medical_or_dietary_restrictions: Optional[List[str]] = Field(default_factory=list, description="Medical/dietary restrictions e.g. Diabetes, High Blood Pressure")
    nutrition_goal: Optional[str] = Field("maintenance", description="Target health goal: weight_loss, weight_gain, maintenance, muscle_gain, healthy_eating")
    daily_calorie_target: Optional[float] = None
    daily_protein_target: Optional[float] = None
    daily_carbs_target: Optional[float] = None
    daily_fat_target: Optional[float] = None
    daily_water_target_ml: Optional[float] = None

    @model_validator(mode='before')
    @classmethod
    def normalize_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "height_cm" in data and "height" not in data:
                data["height"] = data["height_cm"]
            if "weight_kg" in data and "weight" not in data:
                data["weight"] = data["weight_kg"]
            if "target_calories" in data and "daily_calorie_target" not in data:
                data["daily_calorie_target"] = data["target_calories"]
            if "target_protein_g" in data and "daily_protein_target" not in data:
                data["daily_protein_target"] = data["target_protein_g"]
            if "target_carbs_g" in data and "daily_carbs_target" not in data:
                data["daily_carbs_target"] = data["target_carbs_g"]
            if "target_fat_g" in data and "daily_fat_target" not in data:
                data["daily_fat_target"] = data["target_fat_g"]
            if "target_water_ml" in data and "daily_water_target_ml" not in data:
                data["daily_water_target_ml"] = data["target_water_ml"]
        return data

class ProfileCreate(ProfileBase):
    pass

class ProfileUpdate(ProfileBase):
    pass

class UserProfileUpdateRequest(ProfileBase):
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="User full name")

class ProfileResponse(ProfileBase):
    id: Optional[str] = None
    user_id: str
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    bmi: Optional[float] = None
    bmi_category: Optional[str] = None
    bmr: Optional[float] = None
    tdee: Optional[float] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @model_validator(mode='before')
    @classmethod
    def populate_response_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "height" in data and "height_cm" not in data:
                data["height_cm"] = data["height"]
            if "weight" in data and "weight_kg" not in data:
                data["weight_kg"] = data["weight"]
        return data

class UserProfileResponse(BaseModel):
    user_id: str
    email: Optional[str] = None
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    activity_level: Optional[str] = "Moderately Active"
    dietary_preference: Optional[str] = "Veg"
    food_preferences: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    medical_or_dietary_restrictions: List[str] = Field(default_factory=list)
    nutrition_goal: Optional[str] = "maintenance"
    bmi: Optional[float] = None
    bmi_category: Optional[str] = None
    bmr: Optional[float] = None
    tdee: Optional[float] = None
    daily_calorie_target: Optional[float] = None
    daily_protein_target: Optional[float] = None
    daily_carbs_target: Optional[float] = None
    daily_fat_target: Optional[float] = None
    daily_water_target_ml: Optional[float] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @model_validator(mode='before')
    @classmethod
    def populate_user_profile_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "height" in data and "height_cm" not in data:
                data["height_cm"] = data["height"]
            if "weight" in data and "weight_kg" not in data:
                data["weight_kg"] = data["weight"]
        return data
