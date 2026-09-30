from typing import Dict, Any, Optional, List
from fastapi import HTTPException, status
from app.supabase.client import get_supabase_client, supabase
from app.schemas.profile import ProfileCreate, ProfileUpdate, UserProfileUpdateRequest
from app.schemas.nutrition import NutritionGoalCreate, NutritionGoalUpdate
from app.utils.calculations import (
    calculate_bmi,
    calculate_bmr,
    calculate_tdee,
    calculate_macro_targets
)

# In-memory fallback cache for profile state if remote DB table is pending migration
_PROFILE_CACHE: Dict[str, Dict[str, Any]] = {}

class NutritionService:
    def __init__(self):
        self.supabase = supabase

    def get_or_calculate_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Retrieves user nutrition profile and computes BMI, BMR, TDEE, and macro targets.
        """
        profile_data = _PROFILE_CACHE.get(user_id, {})
        try:
            res = self.supabase.table("nutrition_profiles").select("*").eq("user_id", user_id).execute()
            if res.data:
                profile_data = {**profile_data, **res.data[0]}
                _PROFILE_CACHE[user_id] = profile_data
        except Exception:
            pass

        height = float(profile_data.get("height") or 170.0)
        weight = float(profile_data.get("weight") or 70.0)
        age = int(profile_data.get("age") or 25)
        gender = str(profile_data.get("gender") or "Other")
        activity_level = str(profile_data.get("activity_level") or "Moderately Active")
        nutrition_goal = str(profile_data.get("nutrition_goal") or "maintenance")

        bmi_info = calculate_bmi(weight, height)
        bmr = calculate_bmr(weight, height, age, gender)
        tdee = calculate_tdee(bmr, activity_level)

        # Check for explicit goals in nutrition_goals if not in profile
        try:
            goals_res = self.supabase.table("nutrition_goals").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(1).execute()
            if goals_res.data:
                nutrition_goal = goals_res.data[0].get("goal_type", nutrition_goal)
        except Exception:
            pass

        macro_targets = calculate_macro_targets(tdee, nutrition_goal, weight)

        return {
            "id": profile_data.get("id"),
            "user_id": user_id,
            "age": profile_data.get("age"),
            "gender": profile_data.get("gender"),
            "height": profile_data.get("height"),
            "weight": profile_data.get("weight"),
            "activity_level": profile_data.get("activity_level", "Moderately Active"),
            "dietary_preference": profile_data.get("dietary_preference", "Veg"),
            "food_preferences": profile_data.get("food_preferences", []) or [],
            "allergies": profile_data.get("allergies", []) or [],
            "medical_or_dietary_restrictions": profile_data.get("medical_or_dietary_restrictions", []) or [],
            "nutrition_goal": nutrition_goal,
            "bmi": bmi_info["bmi"],
            "bmi_category": bmi_info["category"],
            "bmr": bmr,
            "tdee": tdee,
            "daily_calorie_target": macro_targets["daily_calorie_target"],
            "daily_protein_target": macro_targets["daily_protein_target"],
            "daily_carbs_target": macro_targets["daily_carbs_target"],
            "daily_fat_target": macro_targets["daily_fat_target"],
            "daily_water_target_ml": macro_targets["daily_water_target_ml"],
            "created_at": profile_data.get("created_at"),
            "updated_at": profile_data.get("updated_at")
        }

    def upsert_profile(self, user_id: str, data: UserProfileUpdateRequest) -> Dict[str, Any]:
        """
        Creates or updates a user profile and returns full calculated targets.
        """
        try:
            profile_dict = data.model_dump(
                exclude={"name", "nutrition_goal"},
                exclude_unset=True
            )
            profile_dict["user_id"] = user_id

            # Update cache
            current_cache = _PROFILE_CACHE.get(user_id, {})
            current_cache.update(profile_dict)
            if data.nutrition_goal:
                current_cache["nutrition_goal"] = data.nutrition_goal
            _PROFILE_CACHE[user_id] = current_cache

            db_columns = {"user_id", "age", "gender", "height", "weight", "activity_level", "dietary_preference", "food_preferences", "allergies", "medical_or_dietary_restrictions"}
            db_profile_payload = {k: v for k, v in profile_dict.items() if k in db_columns}

            # Attempt DB write
            try:
                existing = self.supabase.table("nutrition_profiles").select("id").eq("user_id", user_id).execute()
                if existing.data:
                    res = self.supabase.table("nutrition_profiles").update(db_profile_payload).eq("user_id", user_id).execute()
                    if res.data:
                        current_cache.update(res.data[0])
                else:
                    res = self.supabase.table("nutrition_profiles").insert(db_profile_payload).execute()
                    if res.data:
                        current_cache.update(res.data[0])
            except Exception as db_err:
                err_str = str(db_err)
                if "PGRST205" not in err_str and "schema cache" not in err_str.lower():
                    pass

            if data.nutrition_goal:
                profile_for_goal = self.get_or_calculate_profile(user_id)
                target_weight = float(data.weight or profile_for_goal.get("weight") or 70.0)
                calculated_macros = calculate_macro_targets(
                    float(profile_for_goal.get("tdee") or 2000.0),
                    data.nutrition_goal,
                    target_weight,
                )
                goal_payload = {
                    "user_id": user_id,
                    "goal_type": data.nutrition_goal,
                    "target_weight": target_weight,
                    "daily_calorie_target": calculated_macros["daily_calorie_target"],
                    "daily_protein_target": calculated_macros["daily_protein_target"],
                    "daily_carbs_target": calculated_macros["daily_carbs_target"],
                    "daily_fat_target": calculated_macros["daily_fat_target"],
                }
                try:
                    existing_goal = (
                        self.supabase.table("nutrition_goals")
                        .select("id")
                        .eq("user_id", user_id)
                        .order("created_at", desc=True)
                        .limit(1)
                        .execute()
                    )
                    if existing_goal and existing_goal.data:
                        self.supabase.table("nutrition_goals").update(goal_payload).eq(
                            "id", existing_goal.data[0]["id"]
                        ).execute()
                    else:
                        self.supabase.table("nutrition_goals").insert(goal_payload).execute()
                except Exception as goal_error:
                    pass
                
            return self.get_or_calculate_profile(user_id)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error saving nutrition profile: {str(e)}"
            )

    # ------------------ NUTRITION GOALS ------------------ #
    def get_goals(self, user_id: str) -> List[Dict[str, Any]]:
        try:
            res = self.supabase.table("nutrition_goals").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
            return res.data or []
        except Exception as e:
            err_str = str(e)
            if "PGRST205" in err_str or "schema cache" in err_str.lower():
                return []
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching nutrition goals: {err_str}"
            )

    def create_goal(self, user_id: str, data: NutritionGoalCreate) -> Dict[str, Any]:
        try:
            profile = self.get_or_calculate_profile(user_id)
            goal_type = data.goal_type
            weight = float(data.target_weight or profile.get("weight") or 70.0)
            tdee = float(profile.get("tdee") or 2000.0)
            
            calculated_macros = calculate_macro_targets(tdee, goal_type, weight)
            
            goal_record = {
                "user_id": user_id,
                "goal_type": goal_type,
                "target_weight": data.target_weight or profile.get("weight"),
                "daily_calorie_target": data.daily_calorie_target or calculated_macros["daily_calorie_target"],
                "daily_protein_target": data.daily_protein_target or calculated_macros["daily_protein_target"],
                "daily_carbs_target": data.daily_carbs_target or calculated_macros["daily_carbs_target"],
                "daily_fat_target": data.daily_fat_target or calculated_macros["daily_fat_target"]
            }
            
            res = self.supabase.table("nutrition_goals").insert(goal_record).execute()
            if not res.data:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to save nutrition goal.")
            return res.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error creating nutrition goal: {str(e)}"
            )

    def update_goal(self, user_id: str, goal_id: str, data: NutritionGoalUpdate) -> Dict[str, Any]:
        try:
            update_data = {k: v for k, v in data.model_dump().items() if v is not None}
            if not update_data:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided to update.")
            
            res = (
                self.supabase
                .table("nutrition_goals")
                .update(update_data)
                .eq("id", goal_id)
                .eq("user_id", user_id)
                .execute()
            )
            if not res.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found or unauthorized.")
            return res.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error updating goal: {str(e)}"
            )

nutrition_service = NutritionService()
