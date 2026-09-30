from typing import Dict, Any, List

def calculate_bmi(weight_kg: float, height_cm: float) -> Dict[str, Any]:
    """
    Calculate Body Mass Index (BMI) and categorization.
    """
    if not height_cm or height_cm <= 0 or not weight_kg or weight_kg <= 0:
        return {"bmi": 0.0, "category": "Unknown"}
    
    height_m = height_cm / 100.0
    bmi = round(weight_kg / (height_m ** 2), 2)
    
    if bmi < 18.5:
        category = "Underweight"
    elif bmi < 25.0:
        category = "Normal weight"
    elif bmi < 30.0:
        category = "Overweight"
    else:
        category = "Obesity"
        
    return {"bmi": bmi, "category": category}

def calculate_bmr(weight_kg: float, height_cm: float, age: int, gender: str) -> float:
    """
    Calculate Basal Metabolic Rate using Mifflin-St Jeor Equation.
    """
    if not weight_kg or not height_cm or not age:
        return 1600.0 # Default base
        
    if gender and gender.lower().startswith("m"):
        # Male: (10 × weight in kg) + (6.25 × height in cm) - (5 × age in years) + 5
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    else:
        # Female/Other: (10 × weight in kg) + (6.25 × height in cm) - (5 × age in years) - 161
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161
        
    return round(max(bmr, 800.0), 2)

def calculate_tdee(bmr: float, activity_level: str) -> float:
    """
    Calculate Total Daily Energy Expenditure based on activity multiplier.
    """
    multipliers = {
        "sedentary": 1.2,
        "lightly active": 1.375,
        "moderately active": 1.55,
        "very active": 1.725,
        "extra active": 1.9
    }
    key = (activity_level or "").strip().lower()
    factor = multipliers.get(key, 1.375)
    return round(bmr * factor, 2)

def calculate_macro_targets(tdee: float, goal_type: str, weight_kg: float = 70.0) -> Dict[str, float]:
    """
    Calculate personalized daily target for calories, protein, carbs, fats, and water.
    """
    goal = (goal_type or "maintenance").lower().replace(" ", "_").replace("-", "_")
    
    if goal == "weight_loss":
        target_calories = max(tdee - 450.0, 1200.0)
        # Higher protein percentage during deficit: 30% protein, 40% carbs, 30% fat
        protein_g = max(round(weight_kg * 1.8, 1), round((target_calories * 0.30) / 4.0, 1))
        fat_g = round((target_calories * 0.25) / 9.0, 1)
        carbs_g = max(round((target_calories - (protein_g * 4 + fat_g * 9)) / 4.0, 1), 50.0)
    elif goal == "weight_gain":
        target_calories = tdee + 400.0
        protein_g = round(weight_kg * 1.6, 1)
        fat_g = round((target_calories * 0.25) / 9.0, 1)
        carbs_g = round((target_calories - (protein_g * 4 + fat_g * 9)) / 4.0, 1)
    elif goal == "muscle_gain":
        target_calories = tdee + 250.0
        # High protein for muscle synthesis: 2.0g per kg bodyweight
        protein_g = round(weight_kg * 2.0, 1)
        fat_g = round((target_calories * 0.25) / 9.0, 1)
        carbs_g = round((target_calories - (protein_g * 4 + fat_g * 9)) / 4.0, 1)
    else: # maintenance or healthy_eating
        target_calories = tdee
        protein_g = round(weight_kg * 1.4, 1)
        fat_g = round((target_calories * 0.28) / 9.0, 1)
        carbs_g = round((target_calories - (protein_g * 4 + fat_g * 9)) / 4.0, 1)
        
    water_ml = round(weight_kg * 35.0, 0) # 35ml per kg bodyweight
    
    return {
        "daily_calorie_target": round(target_calories, 2),
        "daily_protein_target": round(protein_g, 2),
        "daily_carbs_target": round(carbs_g, 2),
        "daily_fat_target": round(fat_g, 2),
        "daily_water_target_ml": round(max(water_ml, 2000.0), 2)
    }

def aggregate_meal_nutrition(items: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate totals for calories, protein, carbs, fats, fiber, and costs from meal items.
    """
    totals = {
        "calories": 0.0,
        "protein": 0.0,
        "carbs": 0.0,
        "fats": 0.0,
        "fiber": 0.0,
        "cost_inr": 0.0
    }
    for item in items:
        qty = float(item.get("quantity", 1.0) or 1.0)
        totals["calories"] += float(item.get("calories", 0.0) or 0.0) * qty
        totals["protein"] += float(item.get("protein", 0.0) or 0.0) * qty
        totals["carbs"] += float(item.get("carbs", 0.0) or 0.0) * qty
        totals["fats"] += float(item.get("fats", 0.0) or 0.0) * qty
        totals["fiber"] += float(item.get("fiber", 0.0) or 0.0) * qty
        totals["cost_inr"] += float(item.get("cost_inr", 0.0) or 0.0) * qty
        
    return {k: round(v, 2) for k, v in totals.items()}
