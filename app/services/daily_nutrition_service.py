from typing import Dict, Any, Optional
from datetime import date as DateType, date
from fastapi import HTTPException, status
from app.supabase.client import get_supabase_client, supabase
from app.schemas.daily_nutrition import DailyNutritionCreate, DailyNutritionSummary
from app.services.nutrition_service import nutrition_service
from app.services.meal_service import meal_service

class DailyNutritionService:
    def __init__(self):
        self.supabase = supabase

    def get_daily_nutrition(self, user_id: str, target_date: Optional[DateType] = None) -> Dict[str, Any]:
        """
        Retrieves daily nutrition record for a given date, calculating aggregate from logged meals if needed.
        """
        lookup_date = target_date or date.today()
        str_date = str(lookup_date)
        
        # 1. Calculate totals from meals logged on that date
        meals = meal_service.get_meals(user_id=user_id, meal_date=lookup_date)
        meal_calories = sum(m.get("total_calories", 0.0) for m in meals)
        meal_protein = sum(m.get("total_protein", 0.0) for m in meals)
        meal_carbs = sum(m.get("total_carbs", 0.0) for m in meals)
        meal_fats = sum(m.get("total_fats", 0.0) for m in meals)
        meal_fiber = sum(m.get("total_fiber", 0.0) for m in meals)

        # 2. Check if a daily_nutrition entry exists (e.g. for water_intake or manual logs)
        entry = None
        try:
            res = self.supabase.table("daily_nutrition").select("*").eq("user_id", user_id).eq("date", str_date).execute()
            entry = res.data[0] if res.data else None
        except Exception:
            entry = None

        water_intake = float(entry.get("water_intake") or 0.0) if entry else 0.0
        
        # Merge values
        total_calories = max(meal_calories, float(entry.get("calories_consumed") or 0.0) if entry else 0.0)
        total_protein = max(meal_protein, float(entry.get("protein_consumed") or 0.0) if entry else 0.0)
        total_carbs = max(meal_carbs, float(entry.get("carbs_consumed") or 0.0) if entry else 0.0)
        total_fats = max(meal_fats, float(entry.get("fats_consumed") or 0.0) if entry else 0.0)
        total_fiber = max(meal_fiber, float(entry.get("fiber_consumed") or 0.0) if entry else 0.0)

        # 3. Fetch targets from user nutrition profile
        profile = nutrition_service.get_or_calculate_profile(user_id)
        calorie_target = float(profile.get("daily_calorie_target") or 2000.0)
        protein_target = float(profile.get("daily_protein_target") or 140.0)
        carbs_target = float(profile.get("daily_carbs_target") or 225.0)
        fat_target = float(profile.get("daily_fat_target") or 65.0)
        water_target = float(profile.get("daily_water_target_ml") or 2500.0)

        cal_pct = round((total_calories / calorie_target * 100.0), 1) if calorie_target > 0 else 0.0
        prot_pct = round((total_protein / protein_target * 100.0), 1) if protein_target > 0 else 0.0

        return {
            "date": lookup_date,
            "calories_consumed": round(total_calories, 1),
            "calorie_target": calorie_target,
            "protein_consumed": round(total_protein, 1),
            "protein_target": protein_target,
            "carbs_consumed": round(total_carbs, 1),
            "carbs_target": carbs_target,
            "fat_consumed": round(total_fats, 1),
            "fat_target": fat_target,
            "fiber_consumed": round(total_fiber, 1),
            "water_intake": round(water_intake, 1),
            "water_target": water_target,
            "calorie_progress_pct": min(cal_pct, 100.0),
            "protein_progress_pct": min(prot_pct, 100.0)
        }

    def log_daily_nutrition(self, user_id: str, data: DailyNutritionCreate) -> Dict[str, Any]:
        """
        Saves or updates daily nutrition / water intake record.
        """
        try:
            log_date = str(data.date or date.today())
            payload = {
                "user_id": user_id,
                "date": log_date,
                "calories_consumed": data.calories_consumed,
                "protein_consumed": data.protein_consumed,
                "carbs_consumed": data.carbs_consumed,
                "fats_consumed": data.fats_consumed,
                "fiber_consumed": data.fiber_consumed,
                "water_intake": data.water_intake
            }
            
            # Upsert
            res = self.supabase.table("daily_nutrition").upsert(payload, on_conflict="user_id,date").execute()
            return self.get_daily_nutrition(user_id=user_id, target_date=data.date or date.today())
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error logging daily nutrition: {str(e)}"
            )

daily_nutrition_service = DailyNutritionService()
