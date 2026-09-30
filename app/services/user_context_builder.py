from typing import Dict, Any, List, Optional
from datetime import date
from app.services.nutrition_service import nutrition_service
from app.services.daily_nutrition_service import daily_nutrition_service
from app.services.meal_service import meal_service

class UserContextBuilder:
    def build_user_context(self, user_id: str, user_name: Optional[str] = None) -> str:
        """
        Builds a comprehensive, non-hallucinated user context for AI prompts.
        Missing fields are explicitly marked as unavailable.
        """
        today = date.today()

        # 1. Profile Data
        profile = nutrition_service.get_or_calculate_profile(user_id=user_id)
        age = profile.get("age")
        height = profile.get("height")
        weight = profile.get("weight")
        gender = profile.get("gender")
        activity_level = profile.get("activity_level")

        # 2. Daily & Goal Nutrition
        daily = daily_nutrition_service.get_daily_nutrition(user_id=user_id, target_date=today)
        
        calorie_target = daily.get("calorie_target")
        protein_target = daily.get("protein_target")
        carbs_target = daily.get("carbs_target")
        fat_target = daily.get("fat_target")
        fiber_target = daily.get("fiber_target", 30.0) # default fiber target recommendation

        cal_consumed = daily.get("calories_consumed", 0.0)
        prot_consumed = daily.get("protein_consumed", 0.0)
        carbs_consumed = daily.get("carbs_consumed", 0.0)
        fat_consumed = daily.get("fat_consumed", 0.0)
        fiber_consumed = daily.get("fiber_consumed", 0.0)

        cal_remaining = max(0.0, (calorie_target or 0.0) - cal_consumed) if calorie_target is not None else "unavailable"
        prot_remaining = max(0.0, (protein_target or 0.0) - prot_consumed) if protein_target is not None else "unavailable"
        carbs_remaining = max(0.0, (carbs_target or 0.0) - carbs_consumed) if carbs_target is not None else "unavailable"
        fat_remaining = max(0.0, (fat_target or 0.0) - fat_consumed) if fat_target is not None else "unavailable"

        # 3. Preferences & Restrictions
        dietary_pref = profile.get("dietary_preference") or "unavailable"
        food_prefs = profile.get("food_preferences") or []
        allergies = profile.get("allergies") or []
        restrictions = profile.get("medical_or_dietary_restrictions") or []

        # 4. Today's Logged Meals
        today_meals = meal_service.get_meals(user_id=user_id, meal_date=today)
        meals_summary: List[str] = []
        for m in today_meals:
            item_names = [i.get("food_name", "") for i in m.get("items", [])]
            m_str = f"{m.get('meal_type', 'Meal')}: {', '.join(item_names)} ({m.get('total_calories', 0)} kcal, {m.get('total_protein', 0)}g protein)"
            meals_summary.append(m_str)

        # 5. Goals
        nutrition_goal = profile.get("nutrition_goal") or "unavailable"
        target_weight = "unavailable"
        goals_list = nutrition_service.get_goals(user_id)
        if goals_list and len(goals_list) > 0:
            target_weight = goals_list[0].get("target_weight", "unavailable")

        # Format Structured Output
        lines = [
            "USER CONTEXT:",
            "--- PROFILE ---",
            f"Age: {age if age is not None else 'unavailable'}",
            f"Height: {f'{height} cm' if height is not None else 'unavailable'}",
            f"Weight: {f'{weight} kg' if weight is not None else 'unavailable'}",
            f"Gender: {gender if gender else 'unavailable'}",
            f"Activity Level: {activity_level if activity_level else 'unavailable'}",
            "",
            "--- NUTRITION TARGETS & INTAKE ---",
            f"Calorie Target: {f'{calorie_target} kcal' if calorie_target is not None else 'unavailable'} | Consumed: {cal_consumed} kcal | Remaining: {cal_remaining}",
            f"Protein Target: {f'{protein_target} g' if protein_target is not None else 'unavailable'} | Consumed: {prot_consumed} g | Remaining: {prot_remaining}",
            f"Carbs Target: {f'{carbs_target} g' if carbs_target is not None else 'unavailable'} | Consumed: {carbs_consumed} g | Remaining: {carbs_remaining}",
            f"Fat Target: {f'{fat_target} g' if fat_target is not None else 'unavailable'} | Consumed: {fat_consumed} g | Remaining: {fat_remaining}",
            f"Fiber Target: {f'{fiber_target} g' if fiber_target is not None else 'unavailable'} | Consumed: {fiber_consumed} g",
            "",
            "--- PREFERENCES ---",
            f"Dietary Preference: {dietary_pref}",
            f"Food Preferences: {', '.join(food_prefs) if food_prefs else 'None recorded'}",
            "",
            "--- RESTRICTIONS ---",
            f"Allergies: {', '.join(allergies) if allergies else 'None recorded'}",
            f"Health Conditions / Restrictions: {', '.join(restrictions) if restrictions else 'None recorded'}",
            "",
            "--- MEALS TODAY ---",
            f"Logged Meals: {'; '.join(meals_summary) if meals_summary else 'No meals logged yet today'}",
            "",
            "--- GOALS ---",
            f"Nutrition Goal: {nutrition_goal}",
            f"Weight Goal: {target_weight if target_weight != 'unavailable' else 'unavailable'}"
        ]

        return "\n".join(lines)

user_context_builder = UserContextBuilder()
